import pathlib
from setuptools import setup

try:
    import re2 as re
except ImportError:
    import re

packages = ["culligan"]

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Pull the version from __init__.py so we don't need to maintain it in multiple places
init_txt = (HERE / packages[0] / "__init__.py").read_text("utf-8")
try:
    version = re.findall(r"^__version__ = ['\"]([^'\"]+)['\"]\r?$", init_txt, re.M)[0]
except IndexError:
    raise RuntimeError('Unable to determine version.')


setup(
    name="culligan",
    version=version,
    description="Python API for Culligan products",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/rewardone/culligan",
    author="Reward One",
    author_email="rewardone@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=packages,
    include_package_data=False,
    install_requires=list(val.strip() for val in open("requirements.txt")),
)