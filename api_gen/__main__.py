""" Convenience CLI """

import os.path
from ast import parse
from argparse import ArgumentParser
from api_gen._parser import get_api
from api_gen._module import map_modules

parser = ArgumentParser(description="Generate representations of exposed Python API's")
parser.add_argument("sources", nargs="+", help="Path to source file.")
args = parser.parse_args()

real_sources = (os.path.realpath(s) for s in args.sources)
for name, path in map_modules(real_sources).iteritems():
    with open(path) as fh:
        content = fh.read()
        module = parse(content)
    print "MODULE:", name, path
    import pprint

    pprint.pprint(tuple(get_api(module)))
