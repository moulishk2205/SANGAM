"""
Candidate retrieval — hybrid lexical + dense, fused by Reciprocal Rank Fusion.

Retrieval answers "which materials could plausibly be related?" and nothing more. It
is tuned for recall; its precision is irrelevant because the comparator decides. A
match the retriever never returns is a match the system can never make, so recall@k
is the number that caps the whole pipeline.

Two channels, because neither is sufficient alone:

  * Dense embeddings understand that `SS` and `STAINLESS STEEL` mean the same thing —
    the thing lexical matching cannot do.
  * Lexical char-n-grams treat `M10X50` as a symbol — the thing dense embeddings
    cannot do, because BPE shatters it into subwords it shares with `M10X75`.

RRF is used rather than a weighted score sum because BM25-style scores are unbounded
positives and cosine similarity is in [-1, 1]; averaging them is meaningless. RRF
needs no tuning and no score normalisation.

The dense channel is optional. If the embedding model is unavailable the retriever
degrades to lexical only and says so, rather than failing — a demo that cannot start
because a model file is missing is a worse failure than a slightly weaker ranking.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..normalise.text import Normalised, normalise, spec_tokens
from ..types import MaterialRecord

RRF_K = 60          # standard; flat enough that tuning it is not worth a hyperparameter


@dataclass
class Candidate:
    record: MaterialRecord
    lexical_score: float = 0.0
    semantic_score: float = 0.0
    fused: float = 0.0
    channels: list[str] = field(default_factory=list)


class _CharNgramIndex:
    """
    TF-IDF over character 4-grams plus atomic spec tokens.

    Char n-grams are typo-robust and, crucially, keep `M10X50` distinguishable from
    `M10X75` — they differ in several 4-grams even though they share most subwords.
    """

    def __init__(self, n: int = 4) -> None:
        self.n = n
        self.docs: list[str] = []
        self.vecs: list[dict[str, float]] = []
        self.df: dict[str, int] = {}

    @staticmethod
    def _grams(text: str, n: int) -> list[str]:
        t = f"  {text}  "
        return [t[i:i + n] for i in range(max(len(t) - n + 1, 0))]

    def _features(self, text: str, extra: list[str]) -> list[str]:
        return self._grams(text, self.n) + [f"§{t}" for t in extra]

    def build(self, texts: list[str], extras: list[list[str]]) -> None:
        self.docs = texts
        raw: list[dict[str, int]] = []
        for text, ex in zip(texts, extras):
            c: dict[str, int] = {}
            for f in self._features(text, ex):
                c[f] = c.get(f, 0) + 1
            raw.append(c)
            for f in c:
                self.df[f] = self.df.get(f, 0) + 1
        n = max(len(texts), 1)
        self.vecs = []
        for c in raw:
            v = {f: (1 + math.log(cnt)) * math.log(n / (1 + self.df.get(f, 0))) for f, cnt in c.items()}
            norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
            self.vecs.append({f: x / norm for f, x in v.items()})

    def query(self, text: str, extra: list[str], top_k: int) -> list[tuple[int, float]]:
        c: dict[str, int] = {}
        for f in self._features(text, extra):
            c[f] = c.get(f, 0) + 1
        n = max(len(self.docs), 1)
        q = {f: (1 + math.log(cnt)) * math.log(n / (1 + self.df.get(f, 0))) for f, cnt in c.items()}
        norm = math.sqrt(sum(x * x for x in q.values())) or 1.0
        q = {f: x / norm for f, x in q.items()}
        scored = []
        for i, v in enumerate(self.vecs):
            if len(q) < len(v):
                s = sum(w * v.get(f, 0.0) for f, w in q.items())
            else:
                s = sum(w * q.get(f, 0.0) for f, w in v.items())
            if s > 0:
                scored.append((i, s))
        scored.sort(key=lambda p: -p[1])
        return scored[:top_k]


class Retriever:
    """Owns the corpus and both indices. Build once, query many times."""

    MODEL_DIR = Path("models/bge-small-en-v1.5")

    def __init__(self, use_embeddings: bool = True) -> None:
        self.records: list[MaterialRecord] = []
        self.norms: list[Normalised] = []
        self._index_of: dict[str, int] = {}
        self.lex = _CharNgramIndex()
        self._model = None
        self._emb: np.ndarray | None = None
        self.embeddings_enabled = False
        if use_embeddings:
            self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            src = str(self.MODEL_DIR) if self.MODEL_DIR.exists() else "BAAI/bge-small-en-v1.5"
            self._model = SentenceTransformer(src)
            self.embeddings_enabled = True
        except Exception as e:  # noqa: BLE001 — degrade, never fail the demo
            print(f"[retriever] dense channel unavailable, lexical only: {type(e).__name__}: {e}")
            self._model = None
            self.embeddings_enabled = False

    # -- build -----------------------------------------------------------------
    def build(self, records: list[MaterialRecord], norms: list[Normalised]) -> None:
        self.records, self.norms = records, norms
        self._index_of = {r.id: i for i, r in enumerate(records)}
        self.lex.build([n.text for n in norms], [spec_tokens(n) for n in norms])
        if self._model is not None:
            self._emb = self._encode([n.text for n in norms])

    # -- vector access ---------------------------------------------------------
    # The visualization needs the actual embeddings, not a proxy for them. Exposed
    # read-only rather than recomputed, so what is plotted is byte-identical to
    # what retrieval ranked on.

    def vector_of(self, record_id: str) -> np.ndarray | None:
        """The stored embedding for an indexed record, or None if dense is off."""
        if self._emb is None:
            return None
        i = self._index_of.get(record_id)
        return None if i is None else self._emb[i]

    def encode_one(self, text: str) -> np.ndarray | None:
        """Embed an ad-hoc string in the same space as the index."""
        return None if self._model is None else self._encode([text])[0]

    def _encode(self, texts: list[str]) -> np.ndarray:
        v = self._model.encode(texts, batch_size=128, normalize_embeddings=True,
                               show_progress_bar=False, convert_to_numpy=True)
        return v.astype(np.float32)

    def semantic_similarity(self, a: str, b: str) -> float | None:
        """
        Cosine between two normalised strings, or None when the dense channel is off.

        None rather than 0.0 on purpose: "no opinion" and "certainly dissimilar" are
        different facts, and the scorer renormalises over the channels that have one.
        """
        if self._model is None:
            return None
        v = self._encode([a, b])
        return float(np.dot(v[0], v[1]))

    # -- query -----------------------------------------------------------------
    def retrieve(self, text: str, top_k: int = 10, pool: int = 50,
                 exclude_id: str | None = None) -> list[Candidate]:
        n = normalise(text)
        lex_hits = self.lex.query(n.text, spec_tokens(n), pool)

        dense_hits: list[tuple[int, float]] = []
        if self._model is not None and self._emb is not None and len(self._emb):
            q = self._encode([n.text])[0]
            sims = self._emb @ q
            order = np.argsort(-sims)[:pool]
            dense_hits = [(int(i), float(sims[i])) for i in order]

        # RRF: rank-based, so the two incompatible score scales never get averaged.
        fused: dict[int, float] = {}
        chan: dict[int, list[str]] = {}
        lex_s: dict[int, float] = {}
        den_s: dict[int, float] = {}
        for rank, (i, s) in enumerate(lex_hits):
            fused[i] = fused.get(i, 0.0) + 1.0 / (RRF_K + rank + 1)
            chan.setdefault(i, []).append("lexical")
            lex_s[i] = s
        for rank, (i, s) in enumerate(dense_hits):
            fused[i] = fused.get(i, 0.0) + 1.0 / (RRF_K + rank + 1)
            chan.setdefault(i, []).append("dense")
            den_s[i] = s

        out: list[Candidate] = []
        for i, f in sorted(fused.items(), key=lambda p: -p[1]):
            rec = self.records[i]
            if exclude_id is not None and rec.id == exclude_id:
                continue
            out.append(Candidate(record=rec, lexical_score=lex_s.get(i, 0.0),
                                 semantic_score=den_s.get(i, 0.0), fused=f,
                                 channels=chan.get(i, [])))
            if len(out) >= top_k:
                break
        return out


def text_similarity(a: str, b: str, n: int = 4) -> float:
    """
    Character n-gram cosine between two normalised strings, with no index.

    The evidence panel compares one specific pair, outside any retrieval context, so it
    cannot borrow a corpus-relative score. This gives that view a real, self-contained
    text-similarity number instead of a zero that would quietly depress the confidence
    of a perfectly good match.

    Unweighted by IDF on purpose: with two documents there is no corpus to estimate
    document frequency from, and a fabricated IDF would be worse than none.
    """
    def grams(t: str) -> dict[str, int]:
        s = f"  {t}  "
        out: dict[str, int] = {}
        for i in range(max(len(s) - n + 1, 0)):
            g = s[i:i + n]
            out[g] = out.get(g, 0) + 1
        return out

    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    dot = sum(v * gb.get(k, 0) for k, v in ga.items())
    na = math.sqrt(sum(v * v for v in ga.values()))
    nb = math.sqrt(sum(v * v for v in gb.values()))
    return dot / (na * nb) if na and nb else 0.0
