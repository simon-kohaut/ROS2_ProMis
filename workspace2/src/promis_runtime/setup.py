from setuptools import find_packages, setup


package_name = "promis_runtime"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="rensh",
    maintainer_email="rensh@example.com",
    description="Python runtime nodes for ProMis and Nav2 simulation.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "fake_base_node = promis_runtime.fake_base_node:main",
            "nav2_goal_bridge = promis_runtime.nav2_goal_bridge:main",
            "promis_map_node = promis_runtime.promis_map_node:main",
            "static_world_map_node = promis_runtime.static_world_map_node:main",
        ],
    },
)

