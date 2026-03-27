import unittest
from types import SimpleNamespace

from robot_platform.validation import (
    cost_to_pgm_pixel,
    infer_corridor,
    probability_to_cost,
    summarize_path,
)


def make_pose(x: float, y: float):
    return SimpleNamespace(
        pose=SimpleNamespace(
            position=SimpleNamespace(x=x, y=y),
        )
    )


class ValidationMathTest(unittest.TestCase):
    def test_probability_to_cost_clamps_and_handles_nan(self) -> None:
        self.assertEqual(probability_to_cost(1.0), 0)
        self.assertEqual(probability_to_cost(0.0), 254)
        self.assertEqual(probability_to_cost(float("nan")), 254)
        self.assertEqual(probability_to_cost(2.0), 0)
        self.assertEqual(probability_to_cost(-1.0), 254)

    def test_cost_to_pgm_pixel_inverts_cost(self) -> None:
        self.assertEqual(cost_to_pgm_pixel(0), 255)
        self.assertEqual(cost_to_pgm_pixel(254), 1)
        self.assertEqual(cost_to_pgm_pixel(999), 1)

    def test_infer_corridor_uses_average_y(self) -> None:
        self.assertEqual(infer_corridor([1.0, 2.0, 3.0]), "top")
        self.assertEqual(infer_corridor([-1.0, -2.0, -3.0]), "bottom")
        self.assertEqual(infer_corridor([0.1, -0.1, 0.2]), "top")

    def test_summarize_path_reports_corridor_and_length(self) -> None:
        path = SimpleNamespace(
            poses=[make_pose(-1.0, 2.0), make_pose(0.0, 2.0), make_pose(1.0, 2.0)]
        )

        summary = summarize_path(path)

        self.assertEqual(summary.corridor, "top")
        self.assertEqual(summary.pose_count, 3)
        self.assertEqual(summary.path_length_m, 2.0)
        self.assertEqual(summary.average_y, 2.0)


if __name__ == "__main__":
    unittest.main()
