""" Common base types """

from collections import namedtuple as _nt

# Arg types

POSITIONAL = 0b0001
KEYWORD    = 0b0010
VARIADIC   = 0b0100
DEFAULT    = 0b1000

# Types

MODULE = "~module"

# Structs

Ref = _nt("Ref", ("path",))

Var = _nt("Var", ("name", "type"))

Arg = _nt("Arg", ("name", "type", "kind"))

Func = _nt("Func", ("name", "args", "returns"))

Class = _nt("Class", ("name", "body"))
