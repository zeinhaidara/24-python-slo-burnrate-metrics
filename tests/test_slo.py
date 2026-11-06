import tempfile
import unittest
from pathlib import Path

from slo import burn_rate, error_budget, load_config, sli


class SliTests(unittest.TestCase):
    def test_sli_fraction_of_good_orders(self):
        self.assertEqual(sli(95, 100), 0.95)

    def test_sli_with_zero_orders_does_not_divide_by_zero(self):
        self.assertEqual(sli(0, 0), 1.0)


class ErrorBudgetTests(unittest.TestCase):
    def test_error_budget_is_one_minus_target(self):
        self.assertAlmostEqual(error_budget(0.99), 0.01)

    def test_error_budget_rejects_target_of_one(self):
        with self.assertRaises(ValueError):
            error_budget(1.0)

    def test_error_budget_rejects_target_of_zero(self):
        with self.assertRaises(ValueError):
            error_budget(0.0)

    def test_error_budget_rejects_target_above_one(self):
        with self.assertRaises(ValueError):
            error_budget(1.5)


class BurnRateTests(unittest.TestCase):
    def test_burn_rate_under_threshold_is_below_one(self):
        # observed SLI (0.995) is better than target (0.99): burning slower than sustainable.
        rate = burn_rate(observed_sli=0.995, target=0.99)
        self.assertLess(rate, 1.0)

    def test_burn_rate_over_threshold_is_above_one(self):
        # observed SLI (0.9) is worse than target (0.99): burning faster than sustainable.
        rate = burn_rate(observed_sli=0.9, target=0.99)
        self.assertGreater(rate, 1.0)

    def test_burn_rate_exact_target_is_exactly_one(self):
        rate = burn_rate(observed_sli=0.99, target=0.99)
        self.assertAlmostEqual(rate, 1.0)

    def test_burn_rate_with_zero_orders_does_not_divide_by_zero(self):
        # sli(0, 0) is 1.0, so burn_rate at target < 1.0 is well-defined (zero burn).
        observed_sli = sli(0, 0)
        rate = burn_rate(observed_sli, target=0.99)
        self.assertEqual(rate, 0.0)

    def test_burn_rate_rejects_target_of_one(self):
        with self.assertRaises(ValueError):
            burn_rate(observed_sli=0.5, target=1.0)


class LoadConfigTests(unittest.TestCase):
    def _write(self, text):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8")
        tmp.write(text)
        tmp.close()
        return Path(tmp.name)

    def test_loads_valid_config(self):
        path = self._write("target: 0.99\nlatency_threshold_seconds: 0.5\nwindows: [1h, 6h]\n")
        try:
            config = load_config(path)
        finally:
            path.unlink()
        self.assertEqual(config["target"], 0.99)
        self.assertEqual(config["windows"], ["1h", "6h"])

    def test_rejects_target_out_of_range(self):
        path = self._write("target: 1.5\nlatency_threshold_seconds: 0.5\nwindows: [1h]\n")
        try:
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            path.unlink()

    def test_rejects_negative_latency_threshold(self):
        path = self._write("target: 0.99\nlatency_threshold_seconds: -1\nwindows: [1h]\n")
        try:
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            path.unlink()

    def test_rejects_empty_windows(self):
        path = self._write("target: 0.99\nlatency_threshold_seconds: 0.5\nwindows: []\n")
        try:
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            path.unlink()

    def test_rejects_non_mapping_config(self):
        path = self._write("- not\n- a\n- mapping\n")
        try:
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            path.unlink()

    def test_example_config_file_is_valid(self):
        example = Path(__file__).resolve().parent.parent / "config" / "slo.example.yaml"
        config = load_config(example)
        self.assertIn("target", config)


if __name__ == "__main__":
    unittest.main()
