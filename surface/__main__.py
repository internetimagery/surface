""" Convenience CLI """

from __future__ import print_function

import sys
import argparse
import surface


def dump(args):
    modules = {}
    for name in args.modules:
        try:
            mod = __import__(name, fromlist=[""])
        except ImportError:
            print(
                "Failed to import '{}'.\nIs the module in your PYTHONPATH?".format(
                    name
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            modules[name] = mod

            import surface

            print(surface.doit(mod))

    print(modules)
    sys.exit(0)


def compare(args):
    print("COMPARE", args)


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
