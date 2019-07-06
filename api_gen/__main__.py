""" Convenience CLI """

import os.path
from ast import parse
from argparse import ArgumentParser
from api_gen._parser import get_api

parser = ArgumentParser(description="Generate representations of exposed Python API's")
parser.add_argument("source", help="Path to source file.")
args = parser.parse_args()

with open(os.path.realpath(args.source)) as fh:
    content = fh.read()
    module = parse(content)
    import pprint

    pprint.pprint(tuple(get_api(module)))
