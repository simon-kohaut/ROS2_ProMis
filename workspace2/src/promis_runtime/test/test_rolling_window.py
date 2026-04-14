import unittest

from promis_runtime.rolling_window import (
    RollingWindowConfig,
    cell_centers,
    make_grid_spec,
)


class RollingWindowTest(unittest.TestCase):
    def test_grid_dimensions_round_up(self):
        config = RollingWindowConfig(width_m=2.1, height_m=1.1, resolution_m=0.5)
        spec = make_grid_spec(0.0, 0.0, config)
        self.assertEqual(spec.width_cells, 5)
        self.assertEqual(spec.height_cells, 3)
        self.assertEqual(spec.cell_count, 15)

    def test_cell_centers_are_row_major(self):
        config = RollingWindowConfig(
            width_m=2.0,
            height_m=2.0,
            resolution_m=1.0,
            snap_to_grid=False,
        )
        spec = make_grid_spec(0.0, 0.0, config)
        self.assertEqual(
            cell_centers(spec),
            [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)],
        )

    def test_origin_snaps_to_grid(self):
        config = RollingWindowConfig(width_m=2.0, height_m=2.0, resolution_m=0.5)
        spec = make_grid_spec(0.13, 0.13, config)
        self.assertAlmostEqual(spec.origin_x % 0.5, 0.0)
        self.assertAlmostEqual(spec.origin_y % 0.5, 0.0)


if __name__ == "__main__":
    unittest.main()

