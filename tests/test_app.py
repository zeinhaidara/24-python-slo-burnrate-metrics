import unittest

from prometheus_client import REGISTRY, generate_latest

import app


class MetricsOutputTests(unittest.TestCase):
    def test_metrics_output_has_histogram_and_counter_with_outcome_label(self):
        app.process_order()
        app.process_order()

        output = generate_latest(REGISTRY).decode("utf-8")

        self.assertIn("orders_processing_seconds_bucket", output)
        self.assertIn("orders_processing_seconds_count", output)
        self.assertIn("orders_total", output)
        # outcome is random (success/failure) - just confirm the label itself is present
        self.assertTrue(
            'outcome="success"' in output or 'outcome="failure"' in output,
            "expected at least one outcome label on the recorded metrics",
        )

    def test_histogram_bucket_boundary_matches_the_slo_threshold(self):
        app.process_order()
        output = generate_latest(REGISTRY).decode("utf-8")
        self.assertIn('le="0.5"', output)


if __name__ == "__main__":
    unittest.main()
