from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

version = "0.1.0a0"

setup(
    name="ward",
    version=version,
    description="A Python 3 test framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/darrenburns/ward",
    author="Darren Burns",
    author_email="darrenb900@gmail.com",
    license="MIT",
    packages=["ward"],
    python_requires=">=3.6",
)
