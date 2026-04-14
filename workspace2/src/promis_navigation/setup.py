from glob import glob

from setuptools import find_packages, setup


package_name = "promis_navigation"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.py")),
        (f"share/{package_name}/launch/include", glob("launch/include/*.py")),
        (f"share/{package_name}/rviz", glob("rviz/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="rensh",
    maintainer_email="rensh@example.com",
    description="Launch and configuration package for ProMis/Nav2 navigation.",
    license="Apache-2.0",
)

