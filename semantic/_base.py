""" Common base types """

from collections import namedtuple

# Types

ANY = "~any"
MODULE = "~module"

# Structs

Ref = namedtuple("Ref", ("path",))

Var = namedtuple("Var", ("name", "type"))

Arg = namedtuple("Arg", ("name", "type", "keyword"))

Func = namedtuple("Func", ("name", "args", "returns"))

Class = namedtuple("Class", ("name", "body"))
