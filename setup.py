from glob import glob

from setuptools import find_packages, setup


package_name = "robot_platform"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            [f"resource/{package_name}"],
        ),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.py")),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (
            f"share/{package_name}/maps/promis_validation",
            glob("maps/promis_validation/*"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="rensh",
    maintainer_email="rensh@example.com",
    description="Robot-agnostic ROS 2 platform interface for commands, state, and Nav2 goals.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "platform_router = robot_platform.platform_router_node:main",
            "nav2_goal_bridge = robot_platform.nav2_goal_bridge_node:main",
            "validate_nav2_path = robot_platform.validation:main",
        ],
    },
)
