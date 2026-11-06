"""SLO math as pure functions - no server, no I/O beyond loading a config file.

SLI: fraction of orders under the latency threshold over a window.
Error budget: 1 - target.
Burn rate: observed error rate / error budget (1.0 = burning exactly as fast as sustainable).
"""

from __future__ import annotations

from pathlib import Path

import yaml


def sli(good_count: int, total_count: int) -> float:
    """Fraction of orders under the latency threshold. 1.0 (fully healthy) with no data yet,
    rather than dividing by zero."""
    if total_count == 0:
        return 1.0
    return good_count / total_count


def error_budget(target: float) -> float:
    """1 - target. target must be strictly between 0 and 1 - at target == 1.0 there is no
    budget at all, and burn_rate would divide by zero."""
    if not (0.0 < target < 1.0):
        raise ValueError(f"target must be between 0 and 1 (exclusive), got {target!r}")
    return 1.0 - target


def burn_rate(observed_sli: float, target: float) -> float:
    """How fast the error budget is being consumed, relative to 1.0 = exactly sustainable.

    error_budget(target) raises for target == 1.0, so this never divides by zero.
    """
    budget = error_budget(target)
    observed_error_rate = 1.0 - observed_sli
    return observed_error_rate / budget


def load_config(path: str | Path) -> dict:
    """Load and validate a config/slo.example.yaml-shaped file."""
    with open(path, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    _validate_config(config)
    return config


def _validate_config(config) -> None:
    if not isinstance(config, dict):
        raise ValueError("config must be a mapping")

    target = config.get("target")
    if not isinstance(target, (int, float)) or isinstance(target, bool) or not (0.0 < target < 1.0):
        raise ValueError(f"target must be a number between 0 and 1 (exclusive), got {target!r}")

    threshold = config.get("latency_threshold_seconds")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or threshold <= 0:
        raise ValueError(f"latency_threshold_seconds must be a positive number, got {threshold!r}")

    windows = config.get("windows")
    if not isinstance(windows, list) or not windows:
        raise ValueError("windows must be a non-empty list")
