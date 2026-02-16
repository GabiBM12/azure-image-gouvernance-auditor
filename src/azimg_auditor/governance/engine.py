from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yaml


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    description: str
    when: Optional[Dict[str, Any]]
    match: Dict[str, Any]


def load_rules(path: str) -> List[Rule]:
    with open(path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}

    rules = []
    for r in doc.get("rules", []):
        rules.append(
            Rule(
                id=r["id"],
                title=r.get("title", r["id"]),
                severity=r.get("severity", "low"),
                description=r.get("description", ""),
                when=r.get("when"),
                match=r["match"],
            )
        )
    return rules


def evaluate_inventory(
    rows: List[Dict[str, Any]],
    rules_path: str,
    *,
    now_utc: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Returns list of finding dicts:
      { ruleId, severity, title, vmName, subscriptionId, resourceGroup, field, actual, expected, message }
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    rules = load_rules(rules_path)

    findings: List[Dict[str, Any]] = []
    for row in rows:
        for rule in rules:
            if rule.when and not _eval_when(rule.when, row, now_utc):
                continue

            hit = _eval_match(rule.match, row, now_utc)
            if not hit:
                continue

            findings.append(
                {
                    "ruleId": rule.id,
                    "severity": rule.severity,
                    "title": rule.title,
                    "description": rule.description,
                    "subscriptionId": row.get("subscriptionId", ""),
                    "resourceGroup": row.get("resourceGroup", ""),
                    "location": row.get("location", ""),
                    "vmName": row.get("vmName", ""),
                    "imageType": row.get("imageType", ""),
                    "imageId": row.get("imageId", ""),
                    "publisher": row.get("publisher", ""),
                    "offer": row.get("offer", ""),
                    "sku": row.get("sku", ""),
                    "version": row.get("version", ""),
                    "timeCreated": row.get("timeCreated", ""),
                    "field": hit.get("field", ""),
                    "actual": hit.get("actual", ""),
                    "expected": hit.get("expected", ""),
                    "message": hit.get("message", ""),
                }
            )

    return findings


def _eval_when(when_block: Dict[str, Any], row: Dict[str, Any], now_utc: datetime) -> bool:
    if "all" in when_block:
        return all(_eval_condition(c, row, now_utc) for c in when_block["all"])
    if "any" in when_block:
        return any(_eval_condition(c, row, now_utc) for c in when_block["any"])
    # single condition form
    return _eval_condition(when_block, row, now_utc)


def _eval_match(match_block: Dict[str, Any], row: Dict[str, Any], now_utc: datetime) -> Optional[Dict[str, Any]]:
    # match block is one condition
    ok = _eval_condition(match_block, row, now_utc)
    if ok:
        return None

    field = match_block.get("field", "")
    op = match_block.get("op", "")
    expected = match_block.get("value", match_block.get("values", ""))

    return {
        "field": field,
        "actual": _get_field(row, field),
        "expected": expected,
        "message": f"Rule failed: {field} {op} {expected}",
    }


def _eval_condition(cond: Dict[str, Any], row: Dict[str, Any], now_utc: datetime) -> bool:
    field = cond.get("field", "")
    op = cond.get("op", "")
    actual = _get_field(row, field)

    # expected can be in "value" or "values"
    if "values" in cond:
        expected = cond["values"]
    else:
        expected = cond.get("value")

    return _apply_op(op, actual, expected, now_utc)


def _get_field(row: Dict[str, Any], field: str) -> Any:
    # simple flat fields only (your inventory is flat)
    return row.get(field)


def _apply_op(op: str, actual: Any, expected: Any, now_utc: datetime) -> bool:
    # Treat None as empty string for string ops
    if actual is None:
        actual_norm = ""
    else:
        actual_norm = actual

    if op == "eq":
        return str(actual_norm) == str(expected)
    if op == "ne":
        return str(actual_norm) != str(expected)

    if op == "contains":
        return str(expected) in str(actual_norm)
    if op == "not_contains":
        return str(expected) not in str(actual_norm)

    if op == "in":
        return str(actual_norm) in [str(x) for x in (expected or [])]
    if op == "not_in":
        return str(actual_norm) not in [str(x) for x in (expected or [])]

    if op == "startswith":
        return str(actual_norm).startswith(str(expected))
    if op == "endswith":
        return str(actual_norm).endswith(str(expected))

    if op == "older_than_days":
        # expected is an int days, actual is ISO string or empty
        days = int(expected)
        dt = _parse_time(actual_norm)
        if not dt:
            # if missing timeCreated, don't flag by default
            return True
        age_days = (now_utc - dt).days
        return age_days <= days  # passes if not older than threshold

    raise ValueError(f"Unsupported operator: {op}")


def _parse_time(value: Any) -> Optional[datetime]:
    s = str(value or "").strip()
    if not s:
        return None

    # Handle "Z"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)