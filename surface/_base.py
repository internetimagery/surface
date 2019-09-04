""" Common base types """

if False:  # type checking
    from typing import *

import sys as _sys
from collections import namedtuple as _nt


# Compatability
PY2 = _sys.version_info.major == 2

# Type used when actual type cannot be determined.
# While typing.Any could be used here, and would be valid
# we need a distinction between explicitly added typing.Any
# so typing additions can be treated differently to typing changes.
UNKNOWN = "~unknown"

# fmt: off
class Kind(object):
    POSITIONAL = 0b0001
    KEYWORD    = 0b0010
    VARIADIC   = 0b0100
    DEFAULT    = 0b1000

class API(object):
    Var     = _nt("Var",     ("name", "type"))
    Arg     = _nt("Arg",     ("name", "type", "kind"))
    Func    = _nt("Func",    ("name", "args", "returns"))
    Class   = _nt("Class",   ("name", "path", "body"))
    Module  = _nt("Module",  ("name", "path", "body"))
    Unknown = _nt("Unknown", ("name", "type", "info"))
# fmt: on

Change = _nt("Change", ("level", "type", "info"))


TYPE_CHARS = r"\w[\w\.]*(?:\[[\w\.,\[\] ]*\])?"
