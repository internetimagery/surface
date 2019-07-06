""" Common base types """

from collections import namedtuple


ANY = "~any"
MODULE = "~module"

Ref = namedtuple("Ref", ("path",))

Var = namedtuple("Var", ("name", "type"))

Arg = namedtuple("Arg", ("name", "type", "keyword"))

Func = namedtuple("Func", ("name", "args", "returns"))
