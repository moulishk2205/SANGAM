"""
Procurement analytics, and the aggregation opportunity.

WHAT THIS IS FOR

Proving two CPSEs hold the same material is only interesting if something
follows from it. This module is the "something": it reads historical purchase
lines, groups demand by canonical identity, then widens each group using the
functional-equivalence relation and reports what a combined tender would look
like.

HOW THE OPPORTUNITY IS CALCULATED, AND WHY IT IS NOT A GUESS

The temptation is to assert a percentage saving. We do not, because we have no
basis for one — nobody has run the combined tender.

Instead the estimate is arithmetic over observed facts only:

    opportunity = SUM over buyers of  qty_buyer x (price_buyer - best_price)

where `best_price` is the LOWEST UNIT PRICE ACTUALLY PAID for any material in
the equivalence group, in the observed window. It answers a narrow, checkable
question: *if every buyer in this group had paid what the best-performing buyer
already paid, how much less would have been spent?* Every input is a number in
the data; nothing is modelled.

It is labelled "estimated procurement opportunity", never "savings", and the
denominator is always reported alongside it so the figure can be checked.

WHAT IT DELIBERATELY DOES NOT CLAIM

  * that the best price is achievable at the combined volume (it may be better,
    or worse if the low price came from a small local order)
  * that the buyers' requirements coincide in time
  * anything at all about SOUR or FIRED service, where the equivalence layer
    refuses to rule and the group therefore never widens
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from .db.models import (
    CanonicalMaterial, Mapping, MappingStatus, ProcurementRecord, SourceRecord,
)
from .equivalence import Equivalence, compare

PROCUREMENT_VERSION = "procure-v1"


def rupees(paise: int) -> float:
    return round(paise / 100.0, 2)


@dataclass
class MaterialDemand:
    """Demand for ONE canonical identity, across every organisation."""
    canonical_id: str
    item_name: str
    family: str
    item_class: str
    standard_description: str
    quantity: float = 0.0
    uom: str = "EA"
    spend_paise: int = 0
    lines: int = 0
    by_org: dict[str, dict] = field(default_factory=dict)
    first_order: str | None = None
    last_order: str | None = None

    @property
    def avg_unit_paise(self) -> int:
        return int(self.spend_paise / self.quantity) if self.quantity else 0

    def to_dict(self) -> dict:
        return {
            "canonical_id": self.canonical_id, "item_name": self.item_name,
            "family": self.family, "item_class": self.item_class,
            "standard_description": self.standard_description,
            "quantity": round(self.quantity, 2), "uom": self.uom,
            "spend": rupees(self.spend_paise), "lines": self.lines,
            "avg_unit_price": rupees(self.avg_unit_paise),
            "organisations": sorted(self.by_org),
            "by_org": {o: {"quantity": round(v["qty"], 2),
                           "spend": rupees(v["paise"]),
                           "unit_price": rupees(int(v["paise"] / v["qty"])) if v["qty"] else 0.0,
                           "lines": v["lines"]}
                       for o, v in sorted(self.by_org.items())},
            "first_order": self.first_order, "last_order": self.last_order,
        }


def load_demand(db: DbSession, *, family: str | None = None,
                service_class: str | None = None) -> dict[str, MaterialDemand]:
    """
    Purchase lines -> demand per canonical identity.

    Joined through the LIVE mapping, so a line bought under a CPSE code counts
    towards whatever canonical that code currently resolves to. Unmapped lines
    are excluded rather than bucketed as "unknown": they are real spend, but
    they are not evidence about any identity.
    """
    stmt = (
        select(ProcurementRecord, Mapping.canonical_id, CanonicalMaterial)
        .join(SourceRecord, SourceRecord.id == ProcurementRecord.source_record_id)
        .join(Mapping, Mapping.source_record_id == SourceRecord.id)
        .join(CanonicalMaterial, CanonicalMaterial.id == Mapping.canonical_id)
        .where(Mapping.status == MappingStatus.APPROVED,
               Mapping.effective_to.is_(None))
    )
    if family:
        stmt = stmt.where(CanonicalMaterial.family == family)
    if service_class:
        stmt = stmt.where(ProcurementRecord.service_class == service_class)

    out: dict[str, MaterialDemand] = {}
    for pr, canonical_id, cm in db.execute(stmt).all():
        d = out.get(canonical_id)
        if d is None:
            d = out[canonical_id] = MaterialDemand(
                canonical_id=canonical_id, item_name=cm.item_name,
                family=cm.family or "", item_class=cm.item_class,
                standard_description=cm.standard_description or cm.canonical_text,
                uom=pr.uom)
        d.quantity += pr.quantity
        d.spend_paise += pr.line_value_paise
        d.lines += 1
        o = d.by_org.setdefault(pr.org_id, {"qty": 0.0, "paise": 0, "lines": 0})
        o["qty"] += pr.quantity
        o["paise"] += pr.line_value_paise
        o["lines"] += 1
        stamp = pr.ordered_on.isoformat()
        d.first_order = stamp if d.first_order is None else min(d.first_order, stamp)
        d.last_order = stamp if d.last_order is None else max(d.last_order, stamp)
    return out


def summary(db: DbSession) -> dict:
    """Headline procurement figures. Every number is a COUNT or a SUM."""
    total_lines = db.scalar(select(func.count()).select_from(ProcurementRecord)) or 0
    total_paise = db.scalar(select(func.coalesce(func.sum(
        ProcurementRecord.line_value_paise), 0))) or 0
    orgs = db.scalar(select(func.count(func.distinct(ProcurementRecord.org_id)))) or 0
    window = db.execute(select(func.min(ProcurementRecord.ordered_on),
                               func.max(ProcurementRecord.ordered_on))).first()

    demand = load_demand(db)
    multi = [d for d in demand.values() if len(d.by_org) > 1]
    return {
        "lines": total_lines,
        "spend": rupees(total_paise),
        "organisations": orgs,
        "materials_with_history": len(demand),
        "materials_bought_by_multiple_cpses": len(multi),
        "window": {"from": window[0].isoformat() if window and window[0] else None,
                   "to": window[1].isoformat() if window and window[1] else None},
        "provenance": "SYNTHETIC — generated demonstration data, not real "
                      "government procurement records",
        "version": PROCUREMENT_VERSION,
    }


@dataclass
class AggregationGroup:
    """One set of identities a single tender could satisfy."""
    key: str
    members: list[MaterialDemand]
    covering_id: str
    service_class: str
    rationale: list[dict] = field(default_factory=list)

    @property
    def total_qty(self) -> float:
        return sum(m.quantity for m in self.members)

    @property
    def total_spend_paise(self) -> int:
        return sum(m.spend_paise for m in self.members)

    @property
    def best_unit_paise(self) -> int:
        prices = [m.avg_unit_paise for m in self.members if m.avg_unit_paise > 0]
        return min(prices) if prices else 0

    @property
    def opportunity_paise(self) -> int:
        """SUM qty x (paid - best). Never negative; zero when all paid the best."""
        best = self.best_unit_paise
        if not best:
            return 0
        return sum(max(0, m.avg_unit_paise - best) * int(m.quantity) for m in self.members)

    @property
    def organisations(self) -> list[str]:
        return sorted({o for m in self.members for o in m.by_org})

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "service_class": self.service_class,
            "covering_material": self.covering_id,
            "identities": len(self.members),
            "organisations": self.organisations,
            "aggregatable_quantity": round(self.total_qty, 2),
            "combined_spend": rupees(self.total_spend_paise),
            "best_observed_unit_price": rupees(self.best_unit_paise),
            "estimated_opportunity": rupees(self.opportunity_paise),
            "basis": ("Sum over buyers of quantity x (unit price paid - lowest unit "
                      "price observed in this group). Observed figures only; no "
                      "discount is assumed and no saving is promised."),
            "members": [m.to_dict() for m in self.members],
            "rationale": self.rationale,
        }


def aggregation(db: DbSession, *, service_class: str = "GENERAL",
                min_organisations: int = 2) -> dict:
    """
    Group demand by functional equivalence and report the opportunity.

    Grouping is greedy and single-pass: each identity joins the first group whose
    representative it is equivalent to. Equivalence is not transitive in general
    (A covers B and B covers C does not guarantee A covers C once two axes are
    involved), so every member is compared against the group REPRESENTATIVE
    rather than against any member — which keeps the group genuinely satisfiable
    by one part.
    """
    demand = load_demand(db)
    materials = {
        c.id: c for c in db.scalars(
            select(CanonicalMaterial).where(CanonicalMaterial.id.in_(list(demand)))).all()
    } if demand else {}

    # Only compare within a family; a bolt is never equivalent to a flange, and
    # comparing across families is O(n^2) for a guaranteed negative.
    by_family: dict[str, list[str]] = defaultdict(list)
    for cid, d in demand.items():
        by_family[d.family or "unknown"].append(cid)

    groups: list[AggregationGroup] = []
    for fam, ids in by_family.items():
        # Largest demand first, so the representative is the material most worth
        # standardising onto.
        ids.sort(key=lambda c: -demand[c].quantity)
        placed: set[str] = set()
        for cid in ids:
            if cid in placed:
                continue
            rep = materials.get(cid)
            if rep is None:
                continue
            g = AggregationGroup(key=f"{fam}:{cid}", members=[demand[cid]],
                                 covering_id=cid, service_class=service_class)
            placed.add(cid)
            for other in ids:
                if other in placed:
                    continue
                cand = materials.get(other)
                if cand is None:
                    continue
                r = compare(rep.item_name, rep.attributes,
                            cand.item_name, cand.attributes, service_class)
                if r.verdict is not Equivalence.FUNCTIONALLY_EQUIVALENT:
                    continue
                # Only widen when a single part satisfies both. "left" means the
                # representative covers the candidate, which is what a combined
                # tender on the representative requires.
                if r.covering not in ("left", "both"):
                    continue
                g.members.append(demand[other])
                placed.add(other)
                g.rationale.append({
                    "with": other, "verdict": r.verdict.value,
                    "covering": r.covering, "summary": r.summary,
                    "deltas": [d for d in r.to_dict()["deltas"]
                               if d["kind"] == "substitutable"],
                })
            groups.append(g)

    # Report only what a procurement officer could act on: more than one identity
    # AND more than one organisation. A single CPSE's own duplicates are a data
    # quality finding, not an aggregation opportunity.
    actionable = [g for g in groups
                  if len(g.members) > 1 and len(g.organisations) >= min_organisations]
    actionable.sort(key=lambda g: -g.opportunity_paise)

    return {
        "service_class": service_class,
        "groups_examined": len(groups),
        "aggregation_opportunities": len(actionable),
        "total_estimated_opportunity": rupees(sum(g.opportunity_paise for g in actionable)),
        "total_aggregatable_quantity": round(sum(g.total_qty for g in actionable), 2),
        "groups": [g.to_dict() for g in actionable],
        "note": ("Groups widen only where the equivalence layer confirms one "
                 "material covers the other in this service class. SOUR and "
                 "FIRED service never widen — the layer refuses to rule there."),
        "version": PROCUREMENT_VERSION,
    }


def price_trend(db: DbSession, canonical_id: str) -> dict:
    """Unit price paid over time for one identity, per organisation."""
    rows = db.execute(
        select(ProcurementRecord, SourceRecord.org_id)
        .join(SourceRecord, SourceRecord.id == ProcurementRecord.source_record_id)
        .join(Mapping, Mapping.source_record_id == SourceRecord.id)
        .where(Mapping.canonical_id == canonical_id,
               Mapping.status == MappingStatus.APPROVED,
               Mapping.effective_to.is_(None))
        .order_by(ProcurementRecord.ordered_on)
    ).all()
    points = [{"at": pr.ordered_on.isoformat(), "org": org,
               "unit_price": rupees(pr.unit_price_paise),
               "quantity": pr.quantity, "supplier": pr.supplier}
              for pr, org in rows]
    prices = [p["unit_price"] for p in points]
    return {
        "canonical_id": canonical_id, "points": points,
        "orders": len(points),
        "min_unit_price": min(prices) if prices else None,
        "max_unit_price": max(prices) if prices else None,
        "spread_pct": (round((max(prices) - min(prices)) / min(prices) * 100, 1)
                       if prices and min(prices) else None),
    }
