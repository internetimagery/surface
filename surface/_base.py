""" Common base types """

if False:  # type checking
    from typing import *

import sys
from collections import namedtuple as _nt


# Python 2 compatability
PY2 = sys.version_info.major == 2


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

Var     = _nt("Var",     ("name", "type"))

Arg     = _nt("Arg",     ("name", "type", "kind"))

Func    = _nt("Func",    ("name", "args", "returns"))

Class   = _nt("Class",   ("name", "body"))

Module  = _nt("Module",  ("name", "path", "body"))

Unknown = _nt("Unknown", ("name", "info"))

Change  = _nt("Change",  ("level", "type", "info"))


TYPE_CHARS = r"[\w\.]+(?:[\w\.,\[\] ]+)"

TYPING_ATTRS = set((
    "AbstractSet",
    "Any",
    "AnyStr",
    "AsyncIterable",
    "AsyncIterator",
    "Awaitable",
    "BinaryIO",
    "ByteString",
    "Callable",
    "ClassVar",
    "Collection",
    "Container",
    "ContextManager",
    "Coroutine",
    "DefaultDict",
    "Dict",
    "FrozenSet",
    "Generator",
    "Hashable",
    "IO",
    "ItemsView",
    "Iterable",
    "Iterator",
    "KeysView",
    "List",
    "Mapping",
    "MappingView",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "NamedTuple",
    "Optional",
    "Pattern",
    "Reversible",
    "Sequence",
    "Set",
    "Sized",
    "SupportsAbs",
    "SupportsBytes",
    "SupportsComplex",
    "SupportsFloat",
    "SupportsInt",
    "SupportsRound",
    "Text",
    "TextIO",
    "Tuple",
    "Type",
    "TypeVar",
    "Union",
    "ValuesView",
))
