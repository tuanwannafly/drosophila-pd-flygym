"""Hash and repeated-execution checks for post-processing outputs."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Sequence

import numpy as np


def hash_payload(payload: Any) -> str:
    """Return a stable SHA-256 for a JSON-compatible scientific payload."""

    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def repeated_execution_check(
    operation: Callable[[], Any],
    *,
    repeats: int = 2,
) -> dict[str, Any]:
    """Run a supplied analysis operation repeatedly and compare output hashes."""

    if int(repeats) < 2:
        raise ValueError("repeats must be at least 2")
    hashes = [hash_payload(operation()) for _ in range(int(repeats))]
    return {
        "repeats": int(repeats),
        "hashes": hashes,
        "deterministic": len(set(hashes)) == 1,
        "scope": "Deterministic software-output check for a supplied operation; no simulation is run by this utility.",
    }


def seed_consistency_check(
    operation: Callable[[int], Any],
    seeds: Sequence[int],
) -> dict[str, Any]:
    """Compare repeated outputs for explicitly supplied analysis seeds."""

    records = []
    for seed in seeds:
        first = hash_payload(operation(int(seed)))
        second = hash_payload(operation(int(seed)))
        records.append({"seed": int(seed), "first_hash": first, "second_hash": second, "deterministic": first == second})
    return {"seeds": [int(seed) for seed in seeds], "records": records, "overall_pass": bool(records) and all(item["deterministic"] for item in records), "scope": "Seed consistency for a supplied post-processing operation only."}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    return value


__all__ = ["hash_payload", "repeated_execution_check", "seed_consistency_check"]
