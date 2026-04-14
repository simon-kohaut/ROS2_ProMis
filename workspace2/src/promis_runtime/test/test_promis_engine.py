import unittest

from promis_runtime.promis_engine import DemoLandscapeEngine


class DemoLandscapeEngineTest(unittest.TestCase):
    def test_top_corridor_is_preferred_by_default(self):
        engine = DemoLandscapeEngine(
            {
                "demo": {
                    "preferred_corridor": "top",
                    "wave_amplitude": 0.0,
                    "forbidden_zones": [],
                }
            }
        )
        bottom, top = engine.evaluate([(0.0, -3.0), (0.0, 3.0)])
        self.assertGreater(top, bottom)

    def test_forbidden_zone_reduces_probability(self):
        engine = DemoLandscapeEngine(
            {
                "demo": {
                    "wave_amplitude": 0.0,
                    "forbidden_zones": [
                        {
                            "center": [0.0, 0.0],
                            "radius_m": 2.0,
                            "probability": 0.02,
                        }
                    ],
                }
            }
        )
        center, far = engine.evaluate([(0.0, 0.0), (10.0, 10.0)])
        self.assertLess(center, far)


if __name__ == "__main__":
    unittest.main()

