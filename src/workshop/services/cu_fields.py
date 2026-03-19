"""Helpers for reading normalized values from CU field payloads."""

from __future__ import annotations

from typing import Any


def extract_field_value(fields: dict[str, Any], name: str) -> str:
    """Extract a string value from a CU fields mapping."""
    field = fields.get(name, {})
    if isinstance(field, dict):
        return field.get("valueString") or field.get("value") or field.get("content") or ""
    return str(field) if field else ""
