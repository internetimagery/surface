#!/usr/bin/env python

from distutils.core import setup

setup(
    name="surface",
    version="0.0.1a",
    description="Dump and compare simplified representation of a public api",
    author="Jason Dixon",
    url="https://github.com/internetimagery/surface",
    py_modules=["surface"],
    install_requires=["sigtools"],
    entry_points={"console_scripts": ["surface=surface.__main__"]},
)
