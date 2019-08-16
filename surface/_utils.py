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

LOG = logging.getLogger(__name__)

import_times = {}  # type: Dict[str, float]

# Cache stuff


def import_module(name):  # type: (str) -> Any
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


def get_source(func):  # type: (Any) -> str
    try:
        sig = get_signature(func)
    except ValueError:
        return ""
    if not sig:
        return ""
    sources = sorted(sig.sources["+depths"].items(), key=lambda s: s[1])
    try:
        return inspect.getsource(sources[-1][0]) or ""
    except IOError:
        pass
    except TypeError as err:
        LOG.debug(err)
    return ""


def get_tokens(source):  # type: (str) -> List[tokenize.TokenInfo]
    try:
        if sys.version_info.major == 2:
            lines_str = (line for line in source.splitlines(True))
            tokens = list(tokenize.generate_tokens(lambda: next(lines_str)))
        else:
            lines_bytes = (line.encode("utf-8") for line in source.splitlines(True))
            tokens = list(tokenize.tokenize(lambda: next(lines_bytes)))
    except tokenize.TokenError:
        LOG.debug(traceback.format_exc())
        return []
    return tokens


def normalize_type(type_string, context):  # type: (str, Dict[str, Any]) -> str
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
            parent = context.get(node.id)  # in scope?
            if parent:
                mod = inspect.getmodule(parent)
                if mod:
                    updates[node.col_offset] = mod.__name__
            elif node.id in TYPING_ATTRS:  # special case for typing
                updates[node.col_offset] = "typing"

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
        for i in sorted(updates.keys(), reverse=True):
            type_string = "{}{}.{}".format(type_string[:i], updates[i], type_string[i:])
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
    def __init__(self, size):  # type: (int) -> None
        """ Cache stuff. Up to size (mb) """
        self.size = size * 1000000  # mb to bytes
        self._cache = collections.OrderedDict()
        self._current_size = 0

    def __getitem__(self, key):
        """ Move item to front of the queue """
        item = self._cache.pop(key)
        self._cache[key] = item
        return item[0]

    def __setitem__(self, key, value):
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

    def __delitem__(self, key):
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
                        if inspect.isgetsetdescriptor(d) or inspect.ismemberdescriptor(d):
                            size += cls._get_size(obj.__dict__, seen)
                        break
            if isinstance(obj, dict):
                size += sum(cls._get_size(v, seen) for v in obj.values())
                size += sum(cls._get_size(k, seen) for k in obj.keys())
            elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
                size += sum(cls._get_size(i, seen) for i in obj)

            if hasattr(obj, "__slots__"):  # can have __slots__ with __dict__
                size += sum(
                    cls._get_size(getattr(obj, s), seen)
                    for s in obj.__slots__
                    if hasattr(obj, s)
                )
        except Exception: # This should not cause program to fail.
            LOG.debug(traceback.format_exc())
        return size


_cache_sig = Cache(500)
_empty = object()


def get_signature(func):  # type: (Any) -> Optional[sigtools.Signature]
    func_id = id(func)
    cache_value = _cache_sig.get(func_id, _empty)
    if cache_value is not _empty:
        return cache_value

    # handle bug in funcsigs
    restore_attr = False
    if hasattr(func, "__annotations__") and func.__annotations__ is None:
        func.__annotations__ = {}
        restore_attr = True
    try:
        _cache_sig[func_id] = cache_value = sigtools.signature(func)
    except (SyntaxError, ValueError) as err:
        LOG.debug("Error getting signature for {}".format(func))
        LOG.debug(traceback.format_exc())
        _cache_sig[func_id] = None
        return None
    else:
        return cache_value
    finally:
        if restore_attr:
            func.__annotations__ = None
