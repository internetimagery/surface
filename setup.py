#!/usr/bin/env python

import os.path
from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as handle:
    readme = handle.read()

setup(
    name="surface",
    version="0.0.1a",
    description="Expose and compare representation of a public api. (WIP)",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Jason Dixon",
    url="https://github.com/internetimagery/surface",
    packages=["surface"],
    install_requires=["sigtools"],
    python_requires="2.7,>=3.5",
    license="MIT",
    entry_points={"console_scripts": ["surface=surface.__main__"]},
)
