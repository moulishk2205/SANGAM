"""
Measurements, including the ones that are unflattering.

Calibration is reported with ECE and a full reliability table, because a
calibration claim with no reliability curve is decoration. The point of fitting
a calibrator is that "0.9" starts meaning "right about nine times in ten"; the
only way to show that is to bucket the predictions and count.
"""
from __future__ import annotations

import numpy as np


def prf(p: np.ndarray, y: np.ndarray, t: float) -> dict:
    pred = p >= t
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    tn = int((~pred & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"precision": prec, "recall": rec, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def roc_auc(p: np.ndarray, y: np.ndarray) -> float:
    """
    Rank-based AUC via the Mann-Whitney identity, ties averaged.

    Written out rather than imported so the number is reproducible from this
    file alone, and because it is four lines.
    """
    if len(np.unique(y)) < 2:
        return float("nan")
    order = np.argsort(p, kind="mergesort")
    ranks = np.empty(len(p), dtype=np.float64)
    ranks[order] = np.arange(1, len(p) + 1)

    # average ranks within tied score groups
    sp = p[order]
    i = 0
    while i < len(sp):
        j = i
        while j + 1 < len(sp) and sp[j + 1] == sp[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + j + 2) / 2.0
        i = j + 1

    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def reliability(p: np.ndarray, y: np.ndarray, bins: int = 10
                ) -> tuple[list[dict], float]:
    """
    Bucket predictions and compare predicted vs observed. Returns (rows, ECE).

    ECE is the sample-weighted mean gap between what was predicted and what
    happened. Zero would be perfect; anything under a few percent is a
    calibrator doing its job.
    """
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows: list[dict] = []
    ece = 0.0
    n = len(p)
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        m = (p >= lo) & (p < hi) if i < bins - 1 else (p >= lo) & (p <= hi)
        cnt = int(m.sum())
        if not cnt:
            rows.append({"lo": lo, "hi": hi, "n": 0,
                         "predicted": float("nan"), "observed": float("nan")})
            continue
        pred_mean = float(p[m].mean())
        obs = float(y[m].mean())
        rows.append({"lo": lo, "hi": hi, "n": cnt, "predicted": pred_mean, "observed": obs})
        ece += (cnt / n) * abs(pred_mean - obs)
    return rows, float(ece)
