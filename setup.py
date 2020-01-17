import platform

from setuptools import setup

description = "A modern Python 3 test framework for finding and fixing flaws faster."

with open("README.md", "r") as fh:
    if platform.system() != "Windows":
        long_description = fh.read()
    else:
        long_description = description

setup(
    name="ward",
    use_scm_version={
        "write_to": "_ward_version.py",
        "write_to_template": 'version = "{version}"\n',
    },
    setup_requires=['setuptools_scm'],
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/darrenburns/ward",
    author="Darren Burns",
    author_email="darrenb900@gmail.com",
    license="MIT",
    packages=["ward"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["ward=ward.run:run"]},
    install_requires=[
        "colorama==0.4.1",
        "termcolor==1.1.0",
        "dataclasses==0.6; python_version < '3.7'",
        "click==7.0",
    ],
)
