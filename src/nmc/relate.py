"""
Relationship-map construction for the visualization surface.

Kept out of `api.py` for the same reason scoring is: the HTTP layer stays a
transport, so "nothing in this product is fabricated" remains a property you can
verify by reading two small files rather than by trusting a claim.

Nothing here invents a number.

  * Every score is the engine's own output, unmodified.
  * The 2-D projection is a PCA of the *actual* embeddings the retriever ranked
    on — read out of the index, not recomputed and not approximated.
  * Neighbour weights are real cosines between those same vectors.
  * The relationship band is a total function of the engine's decision and veto
    flags. It adds a name, never a judgement.

Two honesty mechanisms are deliberate and should not be optimised away:

  `projection.fidelity` reports the share of variance the two plotted axes
  actually carry. A 384-dimensional neighbourhood of near-identical bolts does
  not have a faithful 2-D shadow, and a scatter plot that looks structured on
  noise is worse than no scatter plot. The number is returned so the interface
  can say how much of the truth the picture is showing.

  `blockers` lists *every* critical attribute that vetoed a pair, not the first
  one found. Reporting only the first under-reports co-occurring failures, and a
  reviewer who fixes one blocker needs to know the other is waiting.
"""
from __future__ import annotations

import time

import numpy as np

from .extract.templates import ATTRIBUTES, critical_codes, family_for
from .match.engine import T_MATCH, T_NEAR, T_REVIEW, MODEL_VERSION, MatchingEngine
from .types import Decision

# ---------------------------------------------------------------------------
# Relationship bands
# ---------------------------------------------------------------------------
# The product vocabulary the brief asks for — "equivalent" vs "similar" vs
# "potential alternative" — mapped onto conditions the engine actually decides.
# No band is a judgement this module makes; each is a rename of an engine state.
#
# The distinction that matters most is the last two. Both are DISTINCT, and they
# are opposite kinds of DISTINCT: one was never close, the other was extremely
# close on text and was rejected on specification. Collapsing them would hide the
# single most instructive thing this system produces.

RELATIONS: dict[str, dict] = {
    "EQUIVALENT": {
        "label": "Equivalent",
        "meaning": "Every critical attribute is stated on both sides and agrees. "
                   "The engine asserts these are the same material.",
        "tone": "brand",
    },
    "PROBABLE": {
        # NOT "probable alternative". That phrasing asserts substitutability, and
        # this engine has no substitutability model — NEAR_MATCH is a score band,
        # not a fitness judgement. The label states what was actually computed.
        "label": "Close — not confirmed",
        "meaning": "No critical attribute disagrees, but the score is below the identity "
                   "threshold. A reviewer decides; the engine asserts nothing.",
        "tone": "info",
    },
    "REVIEW": {
        "label": "Needs review",
        "meaning": "Either a critical attribute is not stated on one side, or the "
                   "score sits in the middle band. Abstention, not a verdict.",
        "tone": "unknown",
    },
    "SIMILAR": {
        "label": "Similar text only",
        "meaning": "Retrieved because the wording resembles the query, then scored "
                   "below the review floor on specification. Not an alternative.",
        "tone": "neutral",
    },
    "REJECTED": {
        "label": "Rejected on specification",
        "meaning": "A critical attribute genuinely disagrees. Vetoed, so it scores "
                   "exactly zero however similar the text is. Not interchangeable.",
        "tone": "distinct",
    },
}


def relation_of(decision: Decision, vetoed: bool) -> str:
    """Total function over the engine's own output. No thresholds re-derived here."""
    if vetoed:
        return "REJECTED"
    if decision is Decision.MATCH:
        return "EQUIVALENT"
    if decision is Decision.NEAR_MATCH:
        return "PROBABLE"
    if decision is Decision.REVIEW_REQUIRED:
        return "REVIEW"
    return "SIMILAR"


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

def rank_fidelity(high: np.ndarray, low: np.ndarray) -> float:
    """
    Spearman correlation between pairwise distances in 384-D and in the plotted 2-D.

    Explained variance says how much of the *variance* survives projection. This
    says something more directly relevant to a picture: whether the ORDER of
    "what is near what" survives. A plot can carry decent variance and still put
    the wrong neighbour closest, which is precisely the failure mode this product
    exists to prevent, so both numbers are reported.
    """
    from scipy.spatial.distance import pdist
    from scipy.stats import spearmanr
    if len(high) < 4:
        return 0.0
    a, b = pdist(high), pdist(low)
    if not np.ptp(a) or not np.ptp(b):
        return 0.0
    r = spearmanr(a, b).statistic
    return 0.0 if np.isnan(r) else float(r)


def fidelity_verdict(variance: float, rank: float) -> tuple[str, str]:
    """
    The interface's own public downgrade of its own projection.

    Hard bands, applied to whichever measure is worse. A projection is only as
    trustworthy as its weakest guarantee, and an interface that quietly rounds
    that up is doing the thing this project is arguing against.
    """
    worst = min(variance, rank)
    if worst >= 0.85:
        return "USABLE", "Distances in this projection track the real ones closely."
    if worst >= 0.70:
        return "WEAK", "Read the broad grouping only. Individual distances are unreliable."
    return "NOT A DISTANCE MAP", (
        "Two axes cannot carry this neighbourhood. Positions here do not rank "
        "materials, and nothing on this screen is placed using them."
    )


def project(mat: np.ndarray) -> tuple[np.ndarray, float] | None:
    """
    PCA of the real embeddings onto two axes.

    Returns (coords scaled into [-1, 1], fidelity) or None when there is nothing
    meaningful to project. `fidelity` is the fraction of total variance carried
    by the two plotted components — the honest answer to "how much of the real
    geometry is this picture showing?".

    Implemented with `np.linalg.svd` rather than a dependency. scikit-learn's PCA
    would do exactly this and cost 80 MB of wheel for a four-line calculation.
    """
    if mat is None or len(mat) < 3:
        return None
    x = mat - mat.mean(axis=0, keepdims=True)
    try:
        _, s, vt = np.linalg.svd(x, full_matrices=False)
    except np.linalg.LinAlgError:          # non-convergence; degrade, never fail
        return None
    coords = x @ vt[:2].T
    total = float((s ** 2).sum())
    fidelity = float((s[:2] ** 2).sum() / total) if total > 0 else 0.0
    scale = float(np.abs(coords).max()) or 1.0
    return coords / scale, fidelity


def _label(code: str) -> str:
    a = ATTRIBUTES.get(code)
    return a.label if a else code.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Map construction
# ---------------------------------------------------------------------------

def catalogue_sample(engine: MatchingEngine, by_record: dict[str, str],
                     limit: int = 260) -> list[tuple[str, str, str]]:
    """
    One representative source record per canonical material, evenly strided.

    Deterministic — same corpus, same sample, every run. Used as the backdrop of
    the embedding inset so the neighbourhood can be seen in the context of the
    whole catalogue rather than floating in an empty plane.
    """
    first: dict[str, str] = {}
    for r in engine.records:
        nmc = by_record.get(r.id)
        if nmc and nmc not in first:
            first[nmc] = r.id
    ids = [first[k] for k in sorted(first)]
    if len(ids) > limit:
        stride = len(ids) / limit
        ids = [ids[int(i * stride)] for i in range(limit)]
    out = []
    for rid in ids:
        rec = engine.get(rid)
        if rec is not None:
            out.append((rid, rec.item_name or "", family_for(rec.item_name) if rec.item_name else "unknown"))
    return out


def build_map(engine: MatchingEngine, by_record: dict[str, str],
              description: str, top_k: int = 24,
              neighbours_per_node: int = 3,
              catalogue_limit: int = 260) -> dict:
    """
    Run the ordinary pipeline, then describe the result as a relationship map.

    This calls `check_before_create` — the same entry point the Analyse screen
    uses, with no separate path and no separate scoring. If the visualization and
    the analysis ever disagreed about a candidate, one of them would be lying;
    they cannot, because they are the same call.
    """
    t0 = time.perf_counter()
    probe, results = engine.check_before_create(description, top_k=top_k,
                                                pool=max(80, top_k * 3))
    elapsed = (time.perf_counter() - t0) * 1000

    crit_order = critical_codes(probe.item_name) or []
    crit = set(crit_order)
    ref_family = family_for(probe.item_name) if probe.item_name else "unknown"

    nodes: list[dict] = []
    for c in results:
        ex = c.explanation
        agree, disagree, unknown, blockers = [], [], [], []
        for r in ex.rows:
            entry = {"code": r.code, "label": r.label,
                     "source": r.left, "candidate": r.right,
                     "criticality": r.criticality.value, "detail": r.detail}
            if r.verdict.value == "AGREE":
                agree.append(entry)
            elif r.verdict.value == "DISAGREE":
                disagree.append(entry)
                if r.vetoed:
                    blockers.append({"code": r.code, "label": r.label,
                                     "source": r.left, "candidate": r.right,
                                     "detail": r.detail})
            else:
                unknown.append(entry)

        # A critical attribute the query itself never stated. This is why a pair
        # that agrees on everything written down can still only reach REVIEW.
        unstated_critical = [u["code"] for u in unknown if u["code"] in crit]

        nodes.append({
            "record_id": c.record.id,
            "nmc_id": by_record.get(c.record.id),
            "description": c.record.raw_description,
            "normalised": c.record.normalised,
            "org": c.record.org,
            "org_code": c.record.org_code,
            "provenance": c.record.provenance,
            "item_name": c.record.item_name or "UNCLASSIFIED",
            "family": family_for(c.record.item_name) if c.record.item_name else "unknown",
            "decision": ex.decision.value,
            "relation": relation_of(ex.decision, ex.critical_veto),
            "confidence": ex.confidence,
            "semantic_score": ex.semantic_score,
            "lexical_score": ex.lexical_score,
            "attribute_agreement": ex.attribute_agreement,
            # The engine's own text term, exactly as engine.explain() computes it.
            # Returned so the client never has to reproduce a server formula.
            "text_score": round(max(ex.semantic_score, ex.lexical_score), 4),
            "vetoed": ex.critical_veto,
            "veto_reason": ex.veto_reason,
            "blockers": blockers,
            "unstated_critical": unstated_critical,
            "counts": {"agree": ex.n_agree, "disagree": ex.n_disagree, "unknown": ex.n_unknown},
            "raw_score": ex.raw_score,
            "arithmetic": {
                "w_attr": 0.85, "attr": ex.attribute_agreement,
                "w_text": 0.15, "text": round(max(ex.semantic_score, ex.lexical_score), 4),
                "raw": ex.raw_score, "veto": 0 if ex.critical_veto else 1,
                "final": ex.confidence,
            },
            "channels": list(c.channels),
            "agree": agree, "disagree": disagree, "unknown": unknown,
        })

    # --- projection over the actual index vectors ----------------------------
    vecs, rows = [], []
    qv = engine.retriever.encode_one(probe.normalised)
    if qv is not None:
        vecs.append(qv); rows.append(None)
        for i, n in enumerate(nodes):
            v = engine.retriever.vector_of(n["record_id"])
            if v is not None:
                vecs.append(v); rows.append(i)

    projection = {"method": "PCA (SVD) over bge-small-en-v1.5 embeddings",
                  "available": False, "fidelity": 0.0, "rank_fidelity": 0.0,
                  "verdict": "NOT A DISTANCE MAP", "note": "",
                  "catalogue_fidelity": 0.0, "catalogue_size": 0}
    reference_xy = [0.0, 0.0]
    catalogue: list[dict] = []
    if len(vecs) >= 3:
        out = project(np.vstack(vecs))
        if out is not None:
            coords, fidelity = out
            rank = rank_fidelity(np.vstack(vecs), coords)
            verdict, note = fidelity_verdict(fidelity, rank)
            projection = {**projection, "available": True,
                          "fidelity": round(fidelity, 4),
                          "rank_fidelity": round(rank, 4),
                          "verdict": verdict, "note": note}
            reference_xy = [round(float(coords[0][0]), 4), round(float(coords[0][1]), 4)]
            for pos, idx in enumerate(rows):
                if idx is None:
                    continue
                nodes[idx]["px"] = round(float(coords[pos][0]), 4)
                nodes[idx]["py"] = round(float(coords[pos][1]), 4)

        # --- the same neighbourhood, seen against the whole catalogue ---------
        # Fitted over catalogue + query + candidates together so every point
        # shares one basis. The candidates collapsing into a single speck here is
        # not a defect of the plot: at catalogue scale that is where they are.
        sample = catalogue_sample(engine, by_record, catalogue_limit)
        cat_vecs, cat_meta = [], []
        for rid, item, fam in sample:
            v = engine.retriever.vector_of(rid)
            if v is not None:
                cat_vecs.append(v)
                cat_meta.append((rid, item, fam))
        if len(cat_vecs) >= 3:
            merged = project(np.vstack(cat_vecs + vecs))
            if merged is not None:
                cc, cfid = merged
                projection["catalogue_fidelity"] = round(cfid, 4)
                projection["catalogue_size"] = len(cat_meta)
                for i, (rid, item, fam) in enumerate(cat_meta):
                    catalogue.append({
                        "record_id": rid, "item_name": item or "UNCLASSIFIED",
                        "family": fam,
                        "cx": round(float(cc[i][0]), 4),
                        "cy": round(float(cc[i][1]), 4),
                    })
                base = len(cat_meta)
                projection["reference_cxy"] = [round(float(cc[base][0]), 4),
                                               round(float(cc[base][1]), 4)]
                for pos, idx in enumerate(rows):
                    if idx is None:
                        continue
                    nodes[idx]["cx"] = round(float(cc[base + pos][0]), 4)
                    nodes[idx]["cy"] = round(float(cc[base + pos][1]), 4)

    # --- deliberately NOT built: candidate-to-candidate similarity edges -----
    # A text-similarity edge drawn inside a decision instrument re-imports the
    # exact signal the veto exists to override. Measured on this corpus, that
    # channel ranks a vetoed bolt ABOVE a true duplicate — 'SS HEX BOLT M10X25'
    # scores 0.9606 against the query while the correct 'STAINLESS STEEL
    # HEXAGONAL BOLT 10MM X 50MM' scores 0.9604. Any graph that draws edge weight
    # from that number puts the wrong material nearer. So no edges are returned.

    # --- the thesis, measured on THIS result set -----------------------------
    # Not an illustration and not a stored figure: two reductions over the
    # candidates just returned. On a fastener query it typically prints that
    # every cosine threshold admitting the true duplicate also admits several
    # different materials — which is the argument for a gate, made in numbers.
    #
    # Stated against SANGAM's own verdict, never against "ground truth": the
    # engine is not entitled to grade itself and then report the grade as fact.
    def _text(n: dict) -> float:
        return max(n["semantic_score"], n["lexical_score"])

    accepted = [n for n in nodes if not n["vetoed"] and n["relation"] in ("EQUIVALENT", "PROBABLE")]
    rejected = [n for n in nodes if n["vetoed"]]
    floor = min((_text(n) for n in accepted), default=0.0)
    ceiling = max((_text(n) for n in rejected), default=0.0)
    inversions = [n for n in rejected if _text(n) >= floor] if accepted else []
    survivors = [n for n in nodes if not n["vetoed"]]
    spread = (max((n["confidence"] for n in survivors), default=0.0)
              - min((n["confidence"] for n in survivors), default=0.0))
    evidence_stats = {
        # A designed-for degenerate state: on a query like `SS HEX BOLT` every
        # survivor can land within a few thousandths of the same score, and the
        # field becomes one flat line. That is a true fact about the query — it
        # is under-specified — and the interface says so rather than spacing the
        # marks out to look busy.
        "score_spread": round(spread, 4),
        "flat_field": bool(len(survivors) >= 6 and spread < 0.02),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "threshold_floor": round(floor, 4),
        "veto_ceiling": round(ceiling, 4),
        "inversions": len(inversions),
        "inversion_examples": [
            {"description": n["description"], "text": round(_text(n), 4),
             "blockers": [b["label"] for b in n["blockers"]]}
            for n in sorted(inversions, key=lambda n: -_text(n))[:3]
        ],
        "closest_accepted": (
            {"description": min(accepted, key=_text)["description"],
             "text": round(floor, 4)} if accepted else None
        ),
    }

    # --- every critical gate, including the ones that stopped nobody ---------
    # A gate that rejected no candidate on this query is information: it ran, and
    # it passed everyone. Dropping the empty cell would turn that into whitespace.
    gate_first: dict[str, int] = {c: 0 for c in crit_order}
    gate_also: dict[str, int] = {c: 0 for c in crit_order}
    for n in nodes:
        for j, b in enumerate(n["blockers"]):
            if j == 0:
                gate_first[b["code"]] = gate_first.get(b["code"], 0) + 1
            else:
                gate_also[b["code"]] = gate_also.get(b["code"], 0) + 1
    gates = [
        {"code": code, "label": _label(code),
         # `count` is the number this gate stopped FIRST; `also` is the number it
         # would also have stopped had another gate not fired first. veto() short
         # circuits, so reporting only the first under-reports co-occurring
         # failures — and a reviewer who fixes one blocker needs to know.
         "count": gate_first.get(code, 0),
         "also": gate_also.get(code, 0),
         "stated_by_query": bool(probe.attr(code) and probe.attr(code).known)}
        for code in crit_order
    ]

    # --- rejections grouped by the value that caused them --------------------
    # "Length · 100 mm · 4 records" instead of four anonymous marks. The engine
    # short-circuits on the first vetoing row, so a candidate can appear under
    # one group while disagreeing elsewhere too; `also_disagrees` carries that
    # rather than letting a single cause be implied.
    groups: dict[tuple[str, str], dict] = {}
    for n in nodes:
        if not n["blockers"]:
            continue
        b = n["blockers"][0]
        key = (b["code"], b["candidate"])
        g = groups.setdefault(key, {
            "code": b["code"], "label": b["label"], "value": b["candidate"],
            "source_value": b["source"], "detail": b["detail"],
            "records": [], "also_disagrees": 0,
        })
        g["records"].append({"record_id": n["record_id"], "description": n["description"],
                             "org": n["org"], "org_code": n["org_code"],
                             "text": round(_text(n), 4)})
        if len(n["blockers"]) > 1:
            g["also_disagrees"] += 1
    rejection_groups = sorted(
        ({**g, "count": len(g["records"])} for g in groups.values()),
        key=lambda g: (-g["count"], g["label"], g["value"]),
    )

    # --- critical attributes the query itself never stated -------------------
    # The difference between "you did not say" and "the master does not record"
    # decides who has to act: the engineer, or the data steward.
    refine: list[dict] = []
    for code in sorted(crit):
        if probe.attr(code) and probe.attr(code).known:
            continue
        seen: dict[str, int] = {}
        for n in nodes:
            for u in n["unknown"]:
                if u["code"] == code and u["candidate"] not in ("—", ""):
                    seen[u["candidate"]] = seen.get(u["candidate"], 0) + 1
        if seen:
            refine.append({
                "code": code, "label": _label(code),
                "values": [{"value": v, "count": c}
                           for v, c in sorted(seen.items(), key=lambda p: -p[1])][:8],
            })

    def _tally(field: str) -> list[dict]:
        counts: dict[str, int] = {}
        for n in nodes:
            counts[n[field]] = counts.get(n[field], 0) + 1
        return [{"value": k, "count": v} for k, v in sorted(counts.items(), key=lambda p: -p[1])]

    return {
        "query": description,
        "normalised": probe.normalised,
        "item_name": probe.item_name or None,
        "family": ref_family,
        "reference": {
            "attributes": [
                {"code": code, "label": _label(code), "value": str(a.value),
                 "critical": code in crit, "source": a.source,
                 "inferred_unit": a.inferred_unit or None}
                for code, a in probe.attributes.items() if a.known
            ],
            "critical_codes": list(crit_order),
            "unstated_critical": sorted(
                c for c in crit
                if not (probe.attr(c) and probe.attr(c).known)
            ),
            "xy": reference_xy,
        },
        "nodes": nodes,
        "catalogue": catalogue,
        "evidence_stats": evidence_stats,
        "gates": gates,
        "rejection_groups": rejection_groups,
        "refine": refine,
        "projection": projection,
        "facets": {"family": _tally("family"), "item_name": _tally("item_name"),
                   "org": _tally("org"), "relation": _tally("relation")},
        "relations": RELATIONS,
        "thresholds": {"match": T_MATCH, "near": T_NEAR, "review": T_REVIEW},
        "dense_channel": engine.retriever.embeddings_enabled,
        "elapsed_ms": round(elapsed, 2),
        "model_version": MODEL_VERSION,
        # Repeated here rather than assumed: this payload drives a picture, and a
        # picture is exactly where an uncalibrated score gets mistaken for a
        # probability.
        "calibrated": False,
    }
