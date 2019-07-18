""" Convenience CLI """

from __future__ import print_function

import sys
import argparse
import surface
import logging
import functools

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stderr))


def dump(args):
    modules = (
        set(r for m in args.modules for r in surface.recurse(m))
        if args.recurse
        else args.modules
    )

    moduleAPI = {}
    for module in modules:
        try:
            api = surface.get_api(module)
        except ImportError:
            LOG.info(
                "Failed to import '{}'.\nIs the module in your PYTHONPATH?".format(
                    module
                )
            )
            return 1
        else:
            moduleAPI[module] = api

    if not args.output:
        for mod, api in moduleAPI.items():
            sys.stdout.write("[{}]\n".format(mod))
            sys.stdout.write(surface.format_api(api, "    "))
        return 0

    try:
        import cPickle as Pickle
    except ImportError:
        import Pickle
    with open(args.output, "wb") as fh:
        Pickle.dump(moduleAPI)
    LOG.info("Saved API to {}".format(args.output))
    return 0


def compare(args):
    LOG.info("TODO! COMPARE", args)


parser = argparse.ArgumentParser(
    description="Generate representations of publicly exposed Python API's."
)
subparsers = parser.add_subparsers()

dump_parser = subparsers.add_parser("dump", help="Store surface API in a file.")
dump_parser.add_argument("-o", "--output", help="File to store API into.")
dump_parser.add_argument(
    "modules", nargs="+", help="Full import path to module eg: mymodule.submodule"
)
dump_parser.add_argument(
    "-r", "--recurse", action="store_true", help="Recusively read submodules too."
)
dump_parser.set_defaults(func=dump)

compare_parser = subparsers.add_parser(
    "compare", help="Compare two API's and suggest a semantic version."
)
compare_parser.add_argument("old", help="Path to original API file.")
compare_parser.add_argument("new", help="Path to new API file.")
compare_parser.set_defaults(func=compare)

args = parser.parse_args()
sys.exit(args.func(args))
