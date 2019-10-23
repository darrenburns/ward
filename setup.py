from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

version = "0.10.0a0"

setup(
    name="ward",
    version=version,
    description="A Python 3 test framework for finding flaws faster.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/darrenburns/ward",
    author="Darren Burns",
    author_email="darrenb900@gmail.com",
    license="MIT",
    packages=["ward"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["ward=ward.run:run"]},
    install_requires=["colorama==0.4.1", "termcolor==1.1.0", "dataclasses==0.6", "click==7.0"],
)
