import math
import unittest

from promis_runtime.probability_cost import (
    CostConversionConfig,
    occupancy_to_probability,
    probabilities_to_occupancy,
    probability_to_occupancy,
)


class ProbabilityCostTest(unittest.TestCase):
    def test_probability_to_occupancy_is_inverted(self):
        self.assertLess(probability_to_occupancy(0.9), probability_to_occupancy(0.2))

    def test_low_probability_can_be_lethal(self):
        config = CostConversionConfig(lethal_probability_threshold=0.1)
        self.assertEqual(probability_to_occupancy(0.05, config), 100)

    def test_nan_uses_unknown_when_configured(self):
        config = CostConversionConfig(unknown_on_nan=True)
        self.assertEqual(probability_to_occupancy(float("nan"), config), -1)

    def test_batch_conversion(self):
        values = probabilities_to_occupancy([1.0, 0.5, 0.0])
        self.assertEqual(values[0], 0)
        self.assertGreater(values[1], values[0])
        self.assertEqual(values[2], 100)

    def test_unknown_inverse_is_nan(self):
        self.assertTrue(math.isnan(occupancy_to_probability(-1)))


if __name__ == "__main__":
    unittest.main()

