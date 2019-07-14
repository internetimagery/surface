""" Common base types """

from collections import namedtuple as _nt

# Arg types

POSITIONAL = 0b001
KEYWORD = 0b010
VARIADIC = 0b100

# Types

MODULE = "~module"

# Structs

Ref = _nt("Ref", ("path",))

Var = _nt("Var", ("name", "type"))

Arg = _nt("Arg", ("name", "type", "kind"))

Func = _nt("Func", ("name", "args", "returns"))

Class = _nt("Class", ("name", "body"))
