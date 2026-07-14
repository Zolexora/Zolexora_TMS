"""Bulk CSV import.

Deliberately redesigned rather than ported: the original imports module
depended on a two-step R2-object-key flow (upload to R2 out of band, then
validate/confirm against that key) that the project's own status docs
already flagged as disconnected/legacy. Since Render has no direct
equivalent to an R2 binding, this version accepts the file directly on
the validate call (multipart/form-data), which is simpler and removes a
moving part rather than reintroducing one.

CSV columns expected: batch_reference, company_code, account_code, debit,
credit, description, entry_date (YYYY-MM-DD), and optionally
site_code/client_code/vehicle_reg_no/manager_code. Rows sharing the same
batch_reference are grouped into a single journal batch (mirroring a Tally
voucher with multiple ledger lines) and validated as a unit via the same
EntriesService validation used by manual entry -- no duplicated business
rules.

Validated-but-unconfirmed imports are kept in an in-memory dict keyed by a
validation_id. That's fine for a single Render instance; if this is ever
scaled to multiple instances, move this to a shared store (e.g. a Postgres
table) instead -- noted here rather than silently left as a hidden gotcha.
"""
from __future__ import annotations

import csv
import io
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.core.errors import ValidationError

_VALIDATION_TTL_SECONDS = 30 * 60
_validation_store: dict[str, "ValidationSession"] = {}


@dataclass
class ValidationSession:
    company_code: str
    groups: dict[str, list[dict[str, Any]]]
    created_at: float = field(default_factory=time.time)


def _prune_expired() -> None:
    now = time.time()
    expired = [k for k, v in _validation_store.items() if now - v.created_at > _VALIDATION_TTL_SECONDS]
    for k in expired:
        _validation_store.pop(k, None)


def store_validation(company_code: str, groups: dict[str, list[dict[str, Any]]]) -> str:
    _prune_expired()
    validation_id = str(uuid.uuid4())
    _validation_store[validation_id] = ValidationSession(company_code=company_code, groups=groups)
    return validation_id


def get_validation(validation_id: str, company_code: str) -> Optional[ValidationSession]:
    _prune_expired()
    session = _validation_store.get(validation_id)
    if not session or session.company_code != company_code:
        return None
    return session


def pop_validation(validation_id: str, company_code: str) -> Optional[ValidationSession]:
    session = get_validation(validation_id, company_code)
    if session:
        _validation_store.pop(validation_id, None)
    return session


REQUIRED_COLUMNS = {"account_code", "debit", "credit"}


def parse_csv_rows(raw_bytes: bytes) -> dict[str, list[dict[str, Any]]]:
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("File must be UTF-8 encoded CSV") from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValidationError("CSV file has no header row")
    missing = REQUIRED_COLUMNS - {c.strip().lower() for c in reader.fieldnames}
    if missing:
        raise ValidationError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    groups: dict[str, list[dict[str, Any]]] = {}
    for line_number, row in enumerate(reader, start=2):
        normalized = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        reference = normalized.get("batch_reference") or f"row-{line_number}"
        normalized["_line_number"] = line_number
        groups.setdefault(reference, []).append(normalized)
    if not groups:
        raise ValidationError("CSV file contains no data rows")
    return groups
