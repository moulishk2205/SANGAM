"""
The persistent schema.

WHY SQLITE BY DEFAULT

`DATABASE_URL` selects the backend and the schema is written to be portable, but
the default is a SQLite file. A hackathon demo that cannot start without a
Postgres server is a demo that fails at the venue, and STARTUP.md promises the
whole thing runs offline. Nothing here uses a SQLite-only feature: point
`DATABASE_URL` at Postgres and the same migrations apply.

The one capability that genuinely needs Postgres is row-level security, which is
how the authority map should eventually be enforced — permission checked at the
row rather than in an application WHERE clause. Until then the scope check lives
in `authz.py` and is honest about being application-level.

WHAT THE SHAPE IS FOR

Four V1 features were selected earlier, and the schema is laid out so none of
them needs a migration later:

  * Safety class lock  — `CanonicalMaterial.item_class` plus `ItemClassRule`
  * Decision certificates — `Decision` freezes evidence and hash-chains
  * Vintages — `spec_revision` on the identity, and `Mapping` is effective-dated
    and supersedable rather than a bare foreign key
  * Emergency lane — a read path over data already here; no schema of its own

THE ONE RULE THIS SCHEMA ENFORCES

A mapping is never deleted and never edited in place. It is superseded: the old
row keeps its effective range and a new row opens. That is what makes the
history re-servable years later, and it is the reason `Decision` stores the
evidence rather than a foreign key to something that may have changed.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON, Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Timezone-aware. Naive datetimes in an audit trail are a future bug."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ── enumerations ───────────────────────────────────────────────────────────
# Stored as strings rather than integers: a dump of this database should be
# readable without the application that wrote it.

class Role(str, enum.Enum):
    REQUESTER = "REQUESTER"   # proposes; cannot approve
    REVIEWER = "REVIEWER"     # approves within their competence scope
    STEWARD = "STEWARD"       # edits the dictionary, templates, tolerances
    ADMIN = "ADMIN"           # user and organisation administration


class MappingStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class DecisionKind(str, enum.Enum):
    PROPOSE = "PROPOSE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    UNMAP = "UNMAP"
    SUPERSEDE = "SUPERSEDE"


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


# ── identity and authority ─────────────────────────────────────────────────

class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code_prefix: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organisation")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), nullable=False)
    org_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), nullable=False)

    # Permission is a pair, not a role: organisation x commodity family. A
    # reviewer certified on fasteners has no business adjudicating cable, and an
    # empty list means "no families", not "all" — a scope that defaults to
    # everything is not a scope.
    commodity_scope: Mapped[list] = mapped_column(JSON, default=list)

    # Item classes this reviewer may sign off. Safety-class items are barred from
    # auto-match entirely and need an explicitly certified human.
    class_certifications: Mapped[list] = mapped_column(JSON, default=list)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    organisation: Mapped[Organisation] = relationship(back_populates="users")


class Session(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


# ── the material data ──────────────────────────────────────────────────────

class SourceRecord(Base):
    """A material as one organisation actually wrote it. Never edited."""
    __tablename__ = "source_records"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), nullable=False, index=True)
    org_code: Mapped[str] = mapped_column(String(64), default="")
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)

    # Derived, cached so the catalogue can be listed without running the engine.
    # Recomputed on a release promotion, never hand-edited.
    normalised: Mapped[str] = mapped_column(Text, default="")
    item_name: Mapped[str] = mapped_column(String(120), default="", index=True)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    provenance: Mapped[str] = mapped_column(String(40), default="SYNTHETIC_VARIANT")
    ingest_job_id: Mapped[str | None] = mapped_column(ForeignKey("ingest_jobs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (Index("ix_source_org_code", "org_id", "org_code"),)


class CanonicalMaterial(Base):
    """
    One standardized identity.

    `spec_revision` is the vintage axis. Two identities can describe the same
    part under different specification revisions, and that is a real distinction
    rather than a duplicate — it is the difference between "same item" and
    "same item, superseded specification", which the matcher's MATCH/DISTINCT
    binary cannot express on its own.
    """
    __tablename__ = "canonical_materials"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)   # NMC-00000000
    item_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    canonical_text: Mapped[str] = mapped_column(Text, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    # Generated from `attributes` by standard/describe.py, never inherited from a
    # member record. Stored rather than computed on read because it is the
    # procurement-facing text — it appears on tenders and in exports, and it must
    # be identical everywhere it is quoted.
    standard_description: Mapped[str] = mapped_column(Text, default="")

    # Commodity family, denormalised from the item name. Equivalence grouping and
    # the review scope both filter on it, and both are hot paths.
    family: Mapped[str] = mapped_column(String(40), default="", index=True)

    item_class: Mapped[str] = mapped_column(String(60), default="GENERAL", index=True)
    spec_standard: Mapped[str] = mapped_column(String(80), default="")
    spec_revision: Mapped[str] = mapped_column(String(40), default="")
    superseded_by: Mapped[str | None] = mapped_column(
        ForeignKey("canonical_materials.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Mapping(Base):
    """
    A source record's claim on a canonical identity.

    Effective-dated and supersedable rather than a plain foreign key, because
    "this code meant that material until March, and something else after" is a
    fact procurement needs and a nullable column cannot hold. Nothing is ever
    deleted; `effective_to` closes and a new row opens.
    """
    __tablename__ = "mappings"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    source_record_id: Mapped[str] = mapped_column(
        ForeignKey("source_records.id"), nullable=False, index=True)
    canonical_id: Mapped[str] = mapped_column(
        ForeignKey("canonical_materials.id"), nullable=False, index=True)

    status: Mapped[MappingStatus] = mapped_column(
        Enum(MappingStatus, native_enum=False), default=MappingStatus.PROPOSED, index=True)

    # The engine's own numbers at the moment it proposed this. Uncalibrated.
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    decided_by_engine: Mapped[str] = mapped_column(String(40), default="")

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by: Mapped[str | None] = mapped_column(ForeignKey("mappings.id"), nullable=True)

    proposed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    proposed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        # One live claim per source record. Superseded and rejected rows are
        # exempt, which is why this is not a bare unique on source_record_id.
        Index("ix_mapping_live", "source_record_id", "status"),
    )


# ── governance ─────────────────────────────────────────────────────────────

class Decision(Base):
    """
    A decision certificate.

    The evidence is frozen here rather than referenced, because everything it
    refers to will change: the gazetteer gets corrected, the template gains an
    attribute, the model is replaced. An auditor in 2034 needs what was on the
    screen when the officer signed, not what the current engine would say now.

    `prev_hash` / `hash` chain the certificates in order. This is tamper-EVIDENT,
    not tamper-proof: the chain lives in a database we control, so it only proves
    anything once the head is anchored somewhere we do not. Saying otherwise
    would not survive an auditor who knows the difference.
    """
    __tablename__ = "decisions"

    # `seq` is the primary key, not `id`. SQLite only auto-increments an INTEGER
    # PRIMARY KEY, so a non-key autoincrement column silently stays NULL and the
    # insert fails on NOT NULL. It is also the honest key here: the chain is
    # ordered by sequence, and the string id is the public handle.
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)

    kind: Mapped[DecisionKind] = mapped_column(
        Enum(DecisionKind, native_enum=False), nullable=False, index=True)
    mapping_id: Mapped[str | None] = mapped_column(ForeignKey("mappings.id"), nullable=True, index=True)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id"), nullable=True)
    canonical_id: Mapped[str | None] = mapped_column(ForeignKey("canonical_materials.id"), nullable=True)

    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(40), default="")
    actor_scope: Mapped[dict] = mapped_column(JSON, default=dict)   # scope held at that moment
    note: Mapped[str] = mapped_column(Text, default="")

    evidence: Mapped[dict] = mapped_column(JSON, default=dict)      # the full comparison table
    gazetteer_version: Mapped[str] = mapped_column(String(40), default="")
    template_version: Mapped[str] = mapped_column(String(40), default="")
    model_version: Mapped[str] = mapped_column(String(80), default="")

    prev_hash: Mapped[str] = mapped_column(String(64), default="")
    hash: Mapped[str] = mapped_column(String(64), default="", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    """Everything that happened, including reads of sensitive endpoints."""
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(80), default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    ip: Mapped[str] = mapped_column(String(64), default="")


class ItemClassRule(Base):
    """
    The safety class lock.

    An item class in pressure, sour or fired service carries extra critical
    attributes and is barred from automatic approval whatever the score says.
    Configuration rather than code so a steward can extend it without a release.
    """
    __tablename__ = "item_class_rules"

    item_class: Mapped[str] = mapped_column(String(60), primary_key=True)
    label: Mapped[str] = mapped_column(String(160), default="")
    extra_critical: Mapped[list] = mapped_column(JSON, default=list)
    bars_auto_match: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_certification: Mapped[bool] = mapped_column(Boolean, default=False)
    basis: Mapped[str] = mapped_column(String(200), default="")   # e.g. "ASME B16.5"


class Release(Base):
    """
    A versioned set of the artefacts that decide identity.

    Promoting a release must replay affected decisions and surface the ones that
    flip. The row exists now so that history is attributable to a version from
    the first decision, rather than being retrofitted later.
    """
    __tablename__ = "releases"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    gazetteer_version: Mapped[str] = mapped_column(String(40), nullable=False)
    template_version: Mapped[str] = mapped_column(String(40), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promoted_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProcurementRecord(Base):
    """
    One historical purchase line, as a CPSE's ERP would hold it.

    The problem statement asks for analysis of "historical procurement data",
    and without it the platform can prove two CPSEs hold the same material but
    not that anything is gained by noticing. Demand aggregation — the impact the
    statement leads with — is arithmetic over this table.

    Deliberately keyed to the SOURCE RECORD, not to the canonical material. A
    purchase happened against a CPSE's own code at a point in time; attributing
    it directly to a canonical identity would silently rewrite history every
    time a mapping was re-approved. The canonical is reached through the live
    mapping, which is exactly how a real ERP reconciliation works.

    Money is stored in paise as an integer. Float rupees accumulate error across
    a few thousand rows and a procurement figure that does not foot is a
    procurement figure nobody trusts.
    """
    __tablename__ = "procurement_records"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    source_record_id: Mapped[str] = mapped_column(
        ForeignKey("source_records.id"), nullable=False, index=True)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    uom: Mapped[str] = mapped_column(String(12), default="EA")
    unit_price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    line_value_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    ordered_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    supplier: Mapped[str] = mapped_column(String(120), default="")
    plant: Mapped[str] = mapped_column(String(80), default="")
    service_class: Mapped[str] = mapped_column(String(40), default="GENERAL", index=True)
    po_number: Mapped[str] = mapped_column(String(40), default="")

    # Synthetic demonstration data must be able to say so about itself.
    provenance: Mapped[str] = mapped_column(String(40), default="SYNTHETIC")


class IngestJob(Base):
    """A bulk upload. Rows land as SourceRecords referencing this job."""
    __tablename__ = "ingest_jobs"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False), default=JobStatus.QUEUED, index=True)

    total: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    accepted: Mapped[int] = mapped_column(Integer, default=0)
    rejected: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")

    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


__all__ = [
    "Base", "utcnow",
    "Role", "MappingStatus", "DecisionKind", "JobStatus",
    "Organisation", "User", "Session",
    "SourceRecord", "CanonicalMaterial", "Mapping",
    "Decision", "AuditEvent", "ItemClassRule", "Release", "IngestJob",
]
