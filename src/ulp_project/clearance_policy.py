"""Clearance risk policy for PLN vegetation monitoring provisional mode."""

from __future__ import annotations


def clearance_status(clearance_m: float | None) -> dict[str, object]:
    if clearance_m is None:
        return {"status": "INSUFFICIENT_DATA", "reason": "clearance_m is required."}
    if clearance_m <= 0:
        return {"status": "IMMEDIATE_ACTION", "reason": "clearance_m <= 0 means contact or overlap risk."}
    return {"status": "CLEARANCE_PROVIDED_MANUAL", "reason": "Manual/provisional clearance input."}
