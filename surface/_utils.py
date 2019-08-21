""" Useful utilities and python compatability work arounds """

if False:
    from typing import *

import re
import sys
import ast
import time
import types
import inspect
import logging
import tokenize
import importlib
import traceback
import sigtools  # type: ignore
import collections

from surface._base import *

if PY2:
    from funcsigs import _empty as _empty  # type: ignore
else:
    from inspect import _empty as _empty  # type: ignore


LOG = logging.getLogger(__name__)

import_times = {}  # type: Dict[str, float]


def import_module(name):  # type: (str) -> Any
    """ Import a module, and time how long it takes """
    start = time.time()
    try:
        LOG.debug("Importing: {}".format(name))
        return importlib.import_module(name)
    finally:
        if name not in import_times:
            import_times[name] = time.time() - start


def clean_repr(err):  # type: (Any) -> str
    """ Strip out memory parts of an error """
    return re.sub(r"<(.+) at (0x[0-9A-Fa-f]+)>", r"<\1 at memory_address>", str(err))


def get_tokens(source):  # type: (str) -> List[tokenize.TokenInfo]
    """ Tokenize string """
    try:
        if PY2:
            lines_str = (line for line in source.splitlines(True))
            tokens = list(tokenize.generate_tokens(lambda: next(lines_str)))
        else:
            lines_bytes = (line.encode("utf-8") for line in source.splitlines(True))
            tokens = list(tokenize.tokenize(lambda: next(lines_bytes)))
    except tokenize.TokenError:
        LOG.debug(traceback.format_exc())
        return []
    return tokens


def abs_type(type_string, context):  # type: (str, Dict[str, Any]) -> str
    """ Convert local type into absolute, eg MyType -> my_module.MyType """
    # Validate type. If it's not valid, just call it unknown
    try:
        root = ast.parse(type_string).body[0].value  # type: ignore
    except (SyntaxError, AttributeError, IndexError):
        return UNKNOWN

    updates = {}
    stack = [root]
    while stack:
        node = stack.pop()

        # eg: myVariable
        if isinstance(node, ast.Name):
            name = node.id
            value = context.get(name)
            # If variable exists in local scope (it generally should), get its full name.
            if value:
                # If variable is a module, and it was aliased, replace with realname.
                if isinstance(value, types.ModuleType):
                    module = getattr(value, "__name__", "")
                    updates[node.col_offset, node.col_offset + len(name) + 1] = module

                else:
                    # Otherwise it's a type referenced locally.
                    module = getattr(inspect.getmodule(value), "__name__", "")
                    if module:
                        updates[node.col_offset, node.col_offset] = module

            # If variable does not exist in the scope, and it exists in the typing module,
            # it is probably "statically" imported. ie not present in runtime.
            elif name in TYPING_ATTRS:  # special case for typing
                updates[node.col_offset, node.col_offset] = "typing"

        # eg: List[something] or Dict[str, int]
        elif isinstance(node, ast.Subscript):
            stack.append(node.value)
            stack.append(node.slice.value)  # type: ignore

        # eg: val1, val2
        elif isinstance(node, ast.Tuple):
            stack.extend(node.elts)

        # eg: val1.val2
        elif isinstance(node, ast.Attribute):
            stack.append(node.value)

    if updates:
        for in_, out in sorted(updates.keys(), reverse=True):
            replace = updates[in_, out]
            type_string = "{}{}.{}".format(
                type_string[:in_], replace, type_string[out:]
            )
    return type_string


# TODO: xml might be a better representation for this data?
# https://docs.python.org/2/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
# can include comments as well, which would be helpful for creation dates etc.
def to_dict(node):  # type: (Any) -> Any
    """ Break a node structure (above types)
        into a dict representation for serialization."""
    data = {"class": type(node).__name__}  # type: Dict[str, Any]
    for key, val in node._asdict().items():
        if isinstance(val, (Var, Arg, Func, Class, Module, Unknown)):
            data[key] = to_dict(val)
        elif isinstance(val, (tuple, list)):
            data[key] = [to_dict(n) for n in val]
        else:
            data[key] = val
    return data


def from_dict(node):  # type: (Dict[str, Any]) -> Any
    """ Reassemble from a dict """
    # Expand everything
    node = {
        k: tuple(from_dict(n) for n in v) if isinstance(v, (tuple, list)) else v
        for k, v in node.items()
    }
    struct = globals()[node.pop("class")]
    return struct(**node)


class Cache(collections.MutableMapping):
    def __init__(self, size=500):  # type: (int) -> None
        """ Cache stuff. Up to size (mb) """
        self.size = size * 1000000  # mb to bytes
        self._cache = (
            collections.OrderedDict()
        )  # type: collections.OrderedDict[Any, Any]
        self._current_size = 0

    def __getitem__(self, key):  # type: (Any) -> Any
        """ Move item to front of the queue """
        item = self._cache.pop(key)
        self._cache[key] = item
        return item[0]

    def __setitem__(self, key, value):  # type: (Any, Any) -> None
        """ Add new item. Drop old items to make space """
        value_size = self._get_size(value) + self._get_size(key)
        self._current_size += value_size
        try:
            item = self._cache.pop(key)
            self._current_size -= item[1]
        except KeyError:
            pass
        while self._current_size > self.size:
            _, item = self._cache.popitem(last=False)
            self._current_size -= item[1]
        self._cache[key] = value, value_size

    def __len__(self):
        return len(self._cache)

    def __iter__(self):
        return iter(self._cache)

    def __delitem__(self, key):  # type: (Any) -> None
        item = self._cache.pop(key)
        self._current_size -= item[1]

    @classmethod  # https://stackoverflow.com/a/38515297
    def _get_size(cls, obj, seen=None):
        """Recursively finds size of objects in bytes"""
        size = sys.getsizeof(obj)
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        # Important mark as seen *before* entering recursion to gracefully handle
        # self-referential objects
        seen.add(obj_id)
        try:
            if hasattr(obj, "__dict__"):
                for obj_cls in obj.__class__.__mro__:
                    if "__dict__" in obj_cls.__dict__:
                        d = obj_cls.__dict__["__dict__"]
                        if inspect.isgetsetdescriptor(d) or inspect.ismemberdescriptor(
                            d
                        ):
                            size += cls._get_size(obj.__dict__, seen)
                        break
            if isinstance(obj, dict):
                size += sum(cls._get_size(v, seen) for v in obj.values())
                size += sum(cls._get_size(k, seen) for k in obj.keys())
            elif hasattr(obj, "__iter__") and not isinstance(
                obj, (str, bytes, bytearray)
            ):
                size += sum(cls._get_size(i, seen) for i in obj)

            if hasattr(obj, "__slots__"):  # can have __slots__ with __dict__
                size += sum(
                    cls._get_size(getattr(obj, s), seen)
                    for s in obj.__slots__
                    if hasattr(obj, s)
                )
        except Exception:  # This should not cause program to fail.
            LOG.debug("Error get_size in cache")
            LOG.debug(traceback.format_exc())
        return size


class IDCache(object):
    """ Generic object that caches based on input object ID """

    _cache = Cache()
    _empty = object()

    def __new__(cls, item):
        item_id = id(item)
        cache_item = cls._cache.get(item_id, cls._empty)
        if cache_item is cls._empty:
            cls._cache[item_id] = cache_item = super(IDCache, cls).__new__(cls)
        return cache_item


FuncSigArg = collections.namedtuple(
    "FuncSigArg", ("name", "kind", "default", "annotation", "source")
)


class FuncSig(IDCache):
    """ Wrapper around sigtools signature gathering """

    _cache = Cache()
    EMPTY = _empty

    _KIND_MAP = {
        "POSITIONAL_ONLY": POSITIONAL,
        "KEYWORD_ONLY": KEYWORD,
        "POSITIONAL_OR_KEYWORD": POSITIONAL | KEYWORD,
        "VAR_POSITIONAL": POSITIONAL | VARIADIC,
        "VAR_KEYWORD": KEYWORD | VARIADIC,
    }

    def __init__(self, func):  # type: (Any) -> None
        self._func = func
        self._sig = None  # type: Optional[sigtools.Signature]
        self._returns = None
        self._parameters = None

        self._get_signature()
        self._get_parameters()

    def __bool__(self):
        return bool(self._sig)

    __nonzero__ = __bool__

    @property
    def func(self):
        return self._func

    @property
    def context(self):
        return getattr(self._func, "__globals__", {})

    @property
    def parameters(self):  # type: () -> collections.OrderedDict[str, FuncSigArg]
        if self._sig is None or self._parameters is None:
            raise RuntimeError("No signature available")
        return self._parameters

    @property
    def returns(self):  # type: () -> FuncSigArg
        if self._sig is None or self._returns is None:
            raise RuntimeError("No signature available")
        return self._returns

    def _get_signature(self):
        # handle bug in funcsigs
        restore_attr = False
        restore_val = None
        if hasattr(self._func, "__annotations__") and not isinstance(
            self._func.__annotations__, dict
        ):
            restore_val = self._func.__annotations__
            self._func.__annotations__ = {}
            restore_attr = True
        try:
            self._sig = sigtools.signature(self._func)
        except (SyntaxError, ValueError) as err:
            LOG.debug("Error getting signature for {}".format(self._func))
            LOG.debug(traceback.format_exc())
        finally:
            if restore_attr:
                self._func.__annotations__ = restore_val

    def _get_parameters(self):
        if not self._sig:
            return

        self._returns = FuncSigArg(
            "",
            None,
            self.EMPTY,
            self._sig.return_annotation,
            sorted(self._sig.sources["+depths"].items(), key=lambda x: x[1])[-1][0],
        )

        self._parameters = collections.OrderedDict()  # type: Dict[str, FuncSigArg]
        for name, param in self._sig.parameters.items():
            self._parameters[name] = FuncSigArg(
                name,
                self._KIND_MAP[str(param.kind)]
                | (0 if param.default is self.EMPTY else DEFAULT),
                param.default,
                param.annotation,
                (self._sig.sources.get(name) or [self._returns.source])[0],
            )
