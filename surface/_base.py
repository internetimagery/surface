""" Common base types """

from collections import namedtuple as _nt

if False:
    from typing import Any, Dict

# fmt: off

# Arg kind types

POSITIONAL = 0b0001
KEYWORD    = 0b0010
VARIADIC   = 0b0100
DEFAULT    = 0b1000

# Structs

Var     = _nt("Var",     ("name", "type"))

Arg     = _nt("Arg",     ("name", "type", "kind"))

Func    = _nt("Func",    ("name", "args", "returns"))

Class   = _nt("Class",   ("name", "body"))

Module  = _nt("Module",  ("name", "path", "body"))

Unknown = _nt("Unknown", ("name", "info"))

Change  = _nt("Change",  ("level", "type", "info"))

# Helper method

def to_dict(node): # type: (Any) -> Any
    """ Break a node structure (above types)
        into a dict representation for serialization."""
    data = {"class": type(node).__name__} # type: Dict[str, Any]
    for key, val in node._asdict().items():
        if isinstance(val, (Var, Arg, Func, Class, Module, Unknown)):
            data[key] = to_dict(val)
        elif isinstance(val, (tuple, list)):
            data[key] = [to_dict(n) for n in val]
        else:
            data[key] = val
    return data

def from_dict(node): # type: (Dict[str, Any]) -> Any
    """ Reassemble from a dict """
    # Expand everything
    node = {k: tuple(from_dict(n) for n in v) if isinstance(v, (tuple, list)) else v for k, v in node.items()}
    struct = globals()[node.pop("class")]
    return struct(**node)
