""" Common base types """

from collections import namedtuple as _nt

# Types

ANY = "~any"
MODULE = "~module"

# Structs

Ref = _nt("Ref", ("path",))

Var = _nt("Var", ("name", "type"))

Arg = _nt("Arg", ("name", "type", "kind"))

Func = _nt("Func", ("name", "args", "returns"))

Class = _nt("Class", ("name", "body"))
