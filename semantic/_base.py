""" Common base types """

from collections import namedtuple


ANY = "~any"
MODULE = "~module"

Var = namedtuple("Var", ("name", "type"))

Arg = namedtuple("Arg", ("type", "keyword", "optional"))
