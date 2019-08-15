""" Convenience CLI """

if False:  # type checking
    from typing import *

# TODO:

# TODO: check module each step of the way, then if inside a new module, traverse that module,
# to get a real parent/child relationship?
# this will help map to static traversing too!

# [major] Type Changed: surface.compare.(api_old), Was: "typing.Sequence[Module]", Now: "typing.Sequence[surface._base.Module]"
# This is wrong... the original module is used, but it is defined in the init module.
# This means changing the underlying location breaks typing. It should read: "surface.Module"
# this means typing normalization needs to change. If name exists in context, then use context path, else use full module path
# context should be an object, with a path to object, and dict of names / values
# Context.from_module()
# Context.from_class()
# Context.from_function()
# etc
# Path needs to be generated and passed around while Traversing

# add --git command that takes a given directory
# when using "surface dump --git /path/to/folder"
# check for the current commit hash, and use that to store the api
# when using surface compare --git /path/to/folder branch_name
# check the current hash, or else generate one
# then check "git merge-base HEAD branch_name"
# and look for that commit within the provided directory

# TODO:
# Need a more comprehensive type comparison
# at the very least it needs to check for ~unknown within a type.
# eg Optional[~unknown] -> Optional[int]

import re
import sys
import json
import time
import surface
import os.path
import argparse
import logging
import traceback
import functools
from surface.git import Git

# Global logger
LOG = logging.getLogger()

# Prevent pyc files from being generated
sys.dont_write_bytecode = True


def run_dump(args):  # type: (Any) -> int
    start = time.time()
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

    module_api = []
    for module in modules:
        try:
            api = surface.get_api(
                module, args.exclude_modules, args.all_filter, args.depth
            )
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
            module_api.append(api)

    if not args.quiet:
        yellow = ("{}" if args.no_colour else "\033[33m{}\033[0m").format
        for mod in module_api:
            sys.stdout.write(
                "[{}]({}s)\n".format(
                    yellow(mod.path), round(surface.import_times.get(mod.path, 0), 2)
                )
            )
            sys.stdout.write(surface.format_api(mod.body, not args.no_colour, "    "))

    if args.output or args.git:
        serialize = [surface.to_dict(mod) for mod in module_api]
        data = json.dumps(serialize, indent=2)

        if args.output:
            with open(args.output, "w") as handle:
                handle.write(data)
                LOG.info("Saved API to {}".format(args.output))
        if args.git:
            commit = Git.get_commit()
            path = Git.save(commit, args.git, data)
            LOG.info("Saved API to {}".format(path))
    if not args.quiet:
        LOG.info("Took ({})".format(round(time.time() - start, 3)))
    return 0


def run_compare(args):  # type: (Any) -> int

    if args.git:  # We are in git mode!! old / new refer to tree-ish identifiers!
        new_commit = Git.get_commit(args.new)
        old_commit = Git.get_merge_base(args.old, args.new)
        git_path = [path.strip() for path in re.split(r"[,:;]", args.git)]

        new_data = Git.load(new_commit, git_path)
        old_data = Git.load(old_commit, git_path)
    else:
        with open(args.old, "r") as handle:
            old_data = handle.read()
        with open(args.new, "r") as handle:
            new_data = handle.read()

    old_api = sorted(
        (surface.from_dict(mod) for mod in json.loads(old_data)), key=lambda m: m.path
    )  # type: List[surface.Module]
    new_api = sorted(
        (surface.from_dict(mod) for mod in json.loads(new_data)), key=lambda m: m.path
    )  # type: List[surface.Module]

    purple = ("{}" if args.no_colour else "\033[35m{}\033[0m").format
    colours = {
        surface.PATCH: ("{}" if args.no_colour else "\033[36m{}\033[0m").format,
        surface.MINOR: ("{}" if args.no_colour else "\033[32m{}\033[0m").format,
        surface.MAJOR: ("{}" if args.no_colour else "\033[31m{}\033[0m").format,
    }

    highest_level = surface.PATCH
    changes = surface.compare(old_api, new_api)
    for level, change_type, note in changes:
        if not args.quiet:
            LOG.info(
                "[{}] {}: {}".format(colours[level](level), purple(change_type), note)
            )
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


def main():
    # -----------------
    # Global options
    # -----------------
    parser = argparse.ArgumentParser(
        description="Generate representations of publicly exposed Python API's."
    )
    parser.add_argument("--debug", action="store_true", help="Show debug messages.")
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

    args = parser.parse_args()
    LOG.addHandler(logging.StreamHandler(sys.stderr))
    LOG.setLevel(logging.DEBUG if args.debug else logging.INFO)
    LOG.debug("Debug on!")
    if args.rules:
        LOG.info(surface.RULES)
        sys.exit(0)
    try:
        sys.exit(args.func(args))
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as err:
        LOG.debug(traceback.format_exc())
        LOG.warn(str(err))
        if args.pdb:
            import pdb

            pdb.post_mortem()
        sys.exit(1)


main()
