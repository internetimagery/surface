#!/usr/bin/env python

import re
import os.path
from distutils.core import setup


root = os.path.dirname(__file__)
# with open(os.path.join(root, "README.md")) as handle:
#     readme = handle.read()

with open(os.path.join(root, "surface", "__init__.py")) as handle:
    version = re.search(r"__version__ *= *['\"]([^'\"]*)['\"]", handle.read()).group(1)

setup(
    name="surface",
    version=version,
    description="Expose and compare a representation of a modules public api.",
    long_description="See https://github.com/internetimagery/surface",
    #    long_description=readme,
    #    long_description_content_type="text/markdown",
    long_description_content_type="text/plain",
    author="Jason Dixon",
    url="https://github.com/internetimagery/surface",
    keywords=["development", "typing", "api", "semantic", "versioning"],
    packages=["surface"],
    install_requires=["sigtools>=2"],
    # python_requires=">=2.7,>=3.6",
    python_requires=">=2.7",
    license="MIT",
    entry_points={"console_scripts": ["surface=surface.__main__"]},
)
