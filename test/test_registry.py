import unittest

from robot_platform.registry import available_adapters, create_adapter


class RegistryTest(unittest.TestCase):
    def test_available_adapters_contains_builtins(self) -> None:
        adapters = available_adapters()
        self.assertIn("generic_mobile_base", adapters)
        self.assertIn("differential_drive", adapters)
        self.assertIn("turtlebot3", adapters)

    def test_build_config_applies_overrides(self) -> None:
        adapter = create_adapter("turtlebot3")
        config = adapter.build_config(
            robot_name="tb3_01",
            overrides={
                "cmd_vel_topic": "/tb3_01/cmd_vel",
                "base_frame": "base_footprint",
            },
            enable_scan=False,
        )

        self.assertEqual(config.robot_name, "tb3_01")
        self.assertEqual(config.robot_type, "turtlebot3")
        self.assertEqual(config.topics.cmd_vel, "/tb3_01/cmd_vel")
        self.assertIsNone(config.topics.scan)
        self.assertEqual(config.frames.base_frame, "base_footprint")

    def test_unknown_adapter_raises_clear_error(self) -> None:
        with self.assertRaises(ValueError) as context:
            create_adapter("unknown_robot")

        self.assertIn("Available adapters", str(context.exception))


if __name__ == "__main__":
    unittest.main()
