from __future__ import annotations

import hashlib
import os

from pyspark.sql import Column
from pyspark.sql import functions as F


def _salt() -> str:
    """Return the configured PII salt or fail explicitly."""
    salt = os.getenv("PII_HASH_SALT")
    if not salt:
        raise ValueError("PII_HASH_SALT must be set and non-empty")
    return salt


def normalize_msisdn(column: str) -> Column:
    """Normalise un numéro au format E.164 (+...) sans espaces."""
    s = F.regexp_replace(F.trim(F.col(column).cast("string")), r"\s+", "")
    s = F.regexp_replace(s, r"^00", "+")
    return F.when(s.rlike(r"^[1-9]\d{10,14}$"), F.concat(F.lit("+"), s)).otherwise(s)


def hash_value(value: str | None) -> str | None:
    """Return a deterministic SHA-256 hex digest of a normalized value."""
    salt = _salt()
    if value is None:
        return None
    normalized = value.strip().lower()
    return hashlib.sha256((salt + normalized).encode("utf-8")).hexdigest()


def hash_column(column: str) -> Column:
    """Build a Spark expression for hashing a string column with the configured salt."""
    salt = _salt()
    normalized = F.lower(F.trim(F.col(column).cast("string")))
    return F.when(F.col(column).isNull(), F.lit(None)).otherwise(
        F.sha2(F.concat(F.lit(salt), normalized), 256)
    )


def hash_msisdn(column: str) -> Column:
    """Normalise un numéro de téléphone, puis le hache avec le sel (SHA-256)."""
    normalized = normalize_msisdn(column)
    return F.when(normalized.isNull() | (normalized == ""), F.lit(None)).otherwise(
        F.sha2(F.concat(F.lit(_salt()), normalized), 256)
    )
