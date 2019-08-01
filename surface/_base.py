""" Common base types """

if False:  # type checking
    from typing import *


from collections import namedtuple as _nt


# fmt: off

# Type used when actual type cannot be determined.
# While typing.Any could be used here, and would be valid
# we need a distinction between explicitly added typing.Any
# so typing additions can be treated differently to typing changes.
UNKNOWN = "~unknown"

# Arg kind types

POSITIONAL = 0b0001
KEYWORD    = 0b0010
VARIADIC   = 0b0100
DEFAULT    = 0b1000

# Structs

Var     = _nt("Var",     ("name", "type")) # type: Tuple[str, str]

Arg     = _nt("Arg",     ("name", "type", "kind")) # type: Tuple[str, str, int]

Func    = _nt("Func",    ("name", "args", "returns")) # type: Tuple[str, List[Arg], str]

Class   = _nt("Class",   ("name", "body")) # type: Tuple[str, List[Any]]

Module  = _nt("Module",  ("name", "path", "body")) # type: Tuple[str, str, List[Any]]

Unknown = _nt("Unknown", ("name", "info")) # type: Tuple[str, str]

Change  = _nt("Change",  ("level", "type", "info")) # type: Tuple[str, str, str]

# Helper method

# TODO: xml might be a better representation for this data?
# https://docs.python.org/2/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
# can include comments as well, which would be helpful for creation dates etc.


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
