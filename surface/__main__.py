""" Convenience CLI """

from __future__ import print_function

if False:  # type checking
    from typing import *


import re
import sys
import json
import time
import os.path
import argparse
import surface
import logging
import functools


# Prevent pyc files from being generated
sys.dont_write_bytecode = True

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stderr))


def run_dump(args):  # type: (Any) -> int
    pythonpath = (
        os.path.realpath(os.path.expanduser(p.strip()))
        for p in re.split(r"[:;]", args.pythonpath or "")
    )
    for path in pythonpath:
        sys.path.insert(0, path)

    modules = (
        set(r for m in args.modules for r in surface.recurse(m))
        if args.recurse
        else args.modules
    )

    module_api = {}
    for module in modules:
        start = time.time()
        try:
            api = surface.get_api(module, args.exclude_modules)
        except ImportError as err:
            LOG.info(
                (
                    "Failed to import '{}'.\n"
                    "{}\n"
                    "Is the module and all its dependencies in your PYTHONPATH?"
                ).format(module, err)
            )
            return 1
        else:
            elapsed = time.time() - start
            module_api[module] = api

    if not args.quiet:
        yellow = ("{}" if args.no_colour else "\033[33m{}\033[0m").format
        for mod, api in module_api.items():
            sys.stdout.write("[{}]({}s)\n".format(yellow(mod), round(elapsed, 2)))
            sys.stdout.write(surface.format_api(api, not args.no_colour, "    "))

    if not args.output:
        return 0

    with open(args.output, "w") as handle:
        serialize = {k: [surface.to_dict(n) for n in v] for k, v in module_api.items()}
        json.dump(serialize, handle, indent=2)
    LOG.info("Saved API to {}".format(args.output))
    return 0


def run_compare(args):  # type: (Any) -> int

    with open(args.old, "r") as handle:
        old_data = {
            k: [surface.from_dict(n) for n in v] for k, v in json.load(handle).items()
        }

    with open(args.new, "r") as handle:
        new_data = {
            k: [surface.from_dict(n) for n in v] for k, v in json.load(handle).items()
        }

    colours = {
        surface.PATCH: ("{}" if args.no_colour else "\033[32m{}\033[0m").format,
        surface.MINOR: ("{}" if args.no_colour else "\033[33m{}\033[0m").format,
        surface.MAJOR: ("{}" if args.no_colour else "\033[35m{}\033[0m").format,
    }

    highest_level = surface.PATCH
    changes = surface.compare(old_data, new_data)
    for level, change_type, note in changes:
        if not args.quiet:
            LOG.info("{}: {}".format(colours[level](change_type), note))
        if level == surface.MAJOR:
            highest_level = level
        elif level == surface.MINOR and highest_level != surface.MAJOR:
            highest_level = level

    if args.bump:
        sys.stdout.write(surface.bump_semantic_version(highest_level, args.bump))
    else:
        sys.stdout.write(highest_level)
    if args.check and (args.check == highest_level or highest_level == surface.MAJOR):
        return 1
    return 0


parser = argparse.ArgumentParser(
    description="Generate representations of publicly exposed Python API's."
)
parser.add_argument("--debug", action="store_true", help="Show debug messages.")
parser.add_argument("--no-colour", action="store_true", help="Disable coloured output.")
parser.add_argument("-q", "--quiet", action="store_true", help="Produce less output.")
parser.add_argument("-V", "--version", action="version", version=surface.__version__)

subparsers = parser.add_subparsers()

dump_parser = subparsers.add_parser("dump", help="Store surface API in a file.")
dump_parser.add_argument("-o", "--output", help="File to store API into.")
dump_parser.add_argument(
    "modules", nargs="+", help="Full import path to module eg: mymodule.submodule"
)
dump_parser.add_argument(
    "-r", "--recurse", action="store_true", help="Recusively read submodules too."
)
dump_parser.add_argument(
    "-p", "--pythonpath", help="Additional paths to use for imports."
)
dump_parser.add_argument(
    "--exclude-modules",
    action="store_true",
    help="Exclude exposed modules in API. (default False)",
)
dump_parser.add_argument(
    "--no-all-filter",
    action="store_true",
    help="Disable filtering of items when an __all__ attribute is present.",
)
dump_parser.set_defaults(func=run_dump)

compare_parser = subparsers.add_parser(
    "compare", help="Compare two API's and suggest a semantic version."
)
compare_parser.add_argument("old", help="Path to original API file.")
compare_parser.add_argument("new", help="Path to new API file.")
compare_parser.add_argument(
    "-b", "--bump", help="Instead of semantic level, return the version bumped."
)
compare_parser.add_argument(
    "-c",
    "--check",
    choices=[surface.MINOR, surface.MAJOR],
    help="For use in a CI environment. Exit 1 if API bumps version equal or above specified.",
)
compare_parser.set_defaults(func=run_compare)

args = parser.parse_args()
LOG.setLevel(logging.DEBUG if args.debug else logging.INFO)
sys.exit(args.func(args))
