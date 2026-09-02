"""
Who is acting, and what they are allowed to act on.

PASSWORDS

PBKDF2-HMAC-SHA256 from the standard library rather than bcrypt or argon2. Those
are better primitives, but they are compiled dependencies that fail to build on
exactly the machine you are demonstrating from. 240k iterations with a per-user
salt is defensible for a prototype, and the format string carries the algorithm
and iteration count so it can be upgraded without a migration.

This is real hashing, not a placeholder. Nothing here stores a plaintext
password.

AUTHORITY IS A PAIR, NOT A ROLE

A reviewer is not "a reviewer" — they are a reviewer *of a commodity family, at
an organisation*. A CPSE-B reviewer certified on fasteners has no business
adjudicating cable, and no role name can express that. So every authorisation
check takes the subject as well as the verb.

Two limits stated plainly. This is application-level enforcement: the check runs
in Python, so a bug in a query that forgets to call it is a hole. Row-level
security in Postgres is where this belongs eventually, and the schema is shaped
for it. And no role, including ADMIN, may approve a mapping that touches another
organisation's code — that is not an oversight, it is the guarantee the whole
system exists to make.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from .db.models import Role, Session, User, utcnow

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 240_000
SESSION_TTL = timedelta(hours=12)


# ── passwords ──────────────────────────────────────────────────────────────

def hash_password(password: str, *, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, digest = stored.split("$", 3)
    except ValueError:
        return False
    if algo != _ALGO:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters))
    # Constant time: a plain == leaks how much of the digest matched.
    return hmac.compare_digest(dk.hex(), digest)


# ── sessions ───────────────────────────────────────────────────────────────

def open_session(db: DbSession, user: User) -> Session:
    s = Session(
        token=secrets.token_urlsafe(32),
        user_id=user.id,
        expires_at=utcnow() + SESSION_TTL,
    )
    db.add(s)
    db.flush()
    return s


def resolve_session(db: DbSession, token: str | None) -> User | None:
    if not token:
        return None
    s = db.get(Session, token)
    if s is None or s.revoked:
        return None
    # Stored timezone-aware; SQLite hands it back naive, so normalise before
    # comparing or every session looks expired.
    exp = s.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=utcnow().tzinfo)
    if exp < utcnow():
        return None
    user = db.get(User, s.user_id)
    return user if user and user.active else None


def revoke_session(db: DbSession, token: str) -> None:
    s = db.get(Session, token)
    if s:
        s.revoked = True


# ── authority ──────────────────────────────────────────────────────────────

class Denied(Exception):
    """Raised with a reason a human can act on, not a bare 403."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def in_commodity_scope(user: User, family: str) -> bool:
    """
    An empty scope means no families, not all of them.

    A scope that silently defaults to everything is not a scope, and this is the
    single easiest place to accidentally grant blanket authority.
    """
    if user.role in (Role.ADMIN, Role.STEWARD):
        return True
    return bool(family) and family in (user.commodity_scope or [])


def certified_for_class(user: User, item_class: str) -> bool:
    if item_class in ("", "GENERAL"):
        return True
    return item_class in (user.class_certifications or [])


def require_role(user: User, *roles: Role) -> None:
    if user.role not in roles:
        raise Denied(
            f"{user.role.value} cannot perform this action; "
            f"requires {' or '.join(r.value for r in roles)}"
        )


def require_own_org(user: User, org_id: str, *, action: str) -> None:
    """
    The guarantee: nobody maps another organisation's code.

    ADMIN is deliberately not exempt. An administrator who can silently rewrite
    another CPSE's material master is precisely the thing that stops CPSEs from
    joining, and an exception here would quietly undo the promise the product is
    built on. Cross-organisation changes go through proposal and objection, not
    through privilege.
    """
    if user.org_id != org_id:
        raise Denied(
            f"{action} touches {org_id}, and authority over another "
            f"organisation's codes cannot be exercised unilaterally — "
            f"propose it instead, so {org_id} can review."
        )


def approver_check(user: User, *, family: str, item_class: str, org_id: str) -> None:
    """Every condition an approval must satisfy, in one place."""
    require_role(user, Role.REVIEWER, Role.STEWARD, Role.ADMIN)
    require_own_org(user, org_id, action="Approval")
    if not in_commodity_scope(user, family):
        raise Denied(
            f"{user.name} is not certified on '{family}'. "
            f"Scope held: {', '.join(user.commodity_scope or []) or 'none'}."
        )
    if not certified_for_class(user, item_class):
        raise Denied(
            f"'{item_class}' is a controlled item class and requires explicit "
            f"certification. {user.name} holds: "
            f"{', '.join(user.class_certifications or []) or 'none'}."
        )


def find_user_by_email(db: DbSession, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower().strip()))
