from setuptools import setup

version = "0.1.0a0"

setup(
    name="ward",
    version=version,
    description="A Python 3 test framework.",
    url="http://github.com/darrenburns/ward",
    author="Darren Burns",
    author_email="darrenb900@gmail.com",
    license="MIT",
    packages=["ward"],
    python_requires=">=3.6",
    zip_safe=False,
)
