""" Convenience CLI """

if False:  # type checking
    from typing import *


import sys
import argparse
import logging
import traceback

import surface
from surface.cli import profile, run_rules, run_dump, run_compare

# Global logger
LOG = logging.getLogger()

# Prevent pyc files from being generated while importing modules.
sys.dont_write_bytecode = True


def main():
    # -----------------
    # Global options
    # -----------------
    parser = argparse.ArgumentParser(
        description="Generate representations of publicly exposed Python API's."
    )
    parser.add_argument("--debug", action="store_true", help="Show debug messages.")
    parser.add_argument("--profile", help="Run profiler, column to sort.")
    parser.add_argument("--rules", action="store_true", help="Show Semantic Rules.")
    parser.add_argument(
        "--no-colour", action="store_true", help="Disable coloured output."
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Produce less output."
    )
    parser.add_argument(
        "-V", "--version", action="version", version=surface.__version__
    )
    parser.add_argument(
        "--pdb",
        action="store_true",
        help="Jump into a pdb session if encountering a fatal error.",
    )

    # -----------------
    # Dump options
    # -----------------

    subparsers = parser.add_subparsers()

    dump_parser = subparsers.add_parser(
        "dump", help="Scan, display and optionally store surface API in a file."
    )
    dump_parser.add_argument("-o", "--output", help="File to store API into.")
    dump_parser.add_argument(
        "-g",
        "--git",
        help="Directory to store API into, under current git commit hash.",
    )
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
        "--all-filter",
        action="store_true",
        help="Where available, filter API by __all__, same as if imported with *",
    )
    dump_parser.add_argument(
        "--depth", type=int, default=6, help="Limit the spidering to this depth."
    )
    dump_parser.set_defaults(func=run_dump)

    # -----------------
    # Compare options
    # -----------------

    compare_parser = subparsers.add_parser(
        "compare", help="Compare two API's and suggest a semantic version."
    )
    compare_parser.add_argument(
        "-g",
        "--git",
        help=(
            "List of directories separated by (,:;)."
            "Presence of this flag will treat 'old' and 'new' arguments as git branches (tree-ish); "
            "Using the merge base between the two as the 'old' source, and the current commit as the 'new' source."
            "The commits will be searched for in the provided directories."
        ),
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

    # Set logging level to debug if requested
    args = parser.parse_args()
    LOG.addHandler(logging.StreamHandler(sys.stderr))
    LOG.setLevel(logging.DEBUG if args.debug else logging.INFO)
    LOG.debug("Debug on!")

    # If rules was requested. Print them out.
    if args.rules:
        args.func = run_rules

    try:
        with profile(args.profile):
            ret_code = args.func(args)
    except KeyboardInterrupt:
        ret_code = 1
    except Exception as err:
        LOG.debug(traceback.format_exc())
        LOG.warn(str(err))
        if args.pdb:
            import pdb

            pdb.post_mortem()
        ret_code = 1
    sys.exit(ret_code)


main()
