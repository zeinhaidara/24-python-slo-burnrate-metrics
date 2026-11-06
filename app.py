"""Tiny fake order simulator exposing Prometheus metrics - not a real shop.

Serves /metrics on METRICS_PORT (default 8000). Each simulated order records its outcome and
latency so the SLO burn-rate rules in rules/slo-burn.rules.yml have something to evaluate.
"""

from __future__ import annotations

import os
import random
import time

from prometheus_client import Counter, Histogram, start_http_server

DEFAULT_PORT = 8000
FAILURE_RATE = 0.05

# 0.5s is a bucket boundary on purpose - it matches latency_threshold_seconds in
# config/slo.example.yaml, which is what the recording rules in rules/slo-burn.rules.yml read
# as orders_processing_seconds_bucket{le="0.5"}.
LATENCY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

ORDERS_TOTAL = Counter("orders_total", "Total simulated orders processed", ["outcome"])
ORDERS_PROCESSING_SECONDS = Histogram(
    "orders_processing_seconds",
    "Simulated order processing latency in seconds",
    ["outcome"],
    buckets=LATENCY_BUCKETS,
)


def process_order() -> None:
    """Simulate processing one order: a little latency, occasional failure."""
    start = time.monotonic()
    outcome = "failure" if random.random() < FAILURE_RATE else "success"
    time.sleep(random.uniform(0.01, 0.05))
    duration = time.monotonic() - start
    ORDERS_TOTAL.labels(outcome=outcome).inc()
    ORDERS_PROCESSING_SECONDS.labels(outcome=outcome).observe(duration)


def main() -> None:
    port = int(os.environ.get("METRICS_PORT", DEFAULT_PORT))
    start_http_server(port)
    while True:
        process_order()
        time.sleep(1)


if __name__ == "__main__":
    main()
