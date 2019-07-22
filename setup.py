#!/usr/bin/env python

from distutils.core import setup

setup(
    name="surface",
    version="0.0.1a",
    description="Expose and compare representation of a public api. (WIP)",
    author="Jason Dixon",
    url="https://github.com/internetimagery/surface",
    packages=["surface"],
    install_requires=["sigtools"],
    entry_points={"console_scripts": ["surface=surface.__main__"]},
)
