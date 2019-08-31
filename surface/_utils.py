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
import traceback
import sigtools  # type: ignore
import collections

from surface._base import *

if PY2:
    from funcsigs import _empty  # type: ignore
else:
    from inspect import _empty  # type: ignore


LOG = logging.getLogger(__name__)


def clean_repr(err):  # type: (Any) -> str
    """ Strip out memory parts of an error """
    return re.sub(r"<(.+) at (0x[0-9A-Fa-f]+)>", r"<\1 at memory_address>", str(err))


def clamp_string(text, limit=200):  # type: (str, int) -> str
    text_len = len(text)
    if text_len <= limit:
        return text
    cutoff = int(limit * 0.5 - 2)
    return text[:cutoff] + "..." + text[text_len - cutoff :]


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


class Cache(collections.MutableMapping):
    def __init__(self, size=500):  # type: (int) -> None
        """ Cache stuff. Up to size (mb) """
        self.size = size
        self._cache = (
            collections.OrderedDict()
        )  # type: collections.OrderedDict[Any, Any]

    def __getitem__(self, key):  # type: (Any) -> Any
        """ Move item to front of the queue """
        item = self._cache.pop(key)
        self._cache[key] = item
        return item

    def __setitem__(self, key, value):  # type: (Any, Any) -> None
        """ Add new item. Drop old items to make space """
        try:
            self._cache.pop(key)
        except KeyError:
            if len(self._cache) > self.size:
                self._cache.popitem(last=False)
        self._cache[key] = value

    def __len__(self):
        return len(self._cache)

    def __iter__(self):
        return iter(self._cache)

    def __delitem__(self, key):  # type: (Any) -> None
        del self._cache[key]


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
    "FuncSigArg", ("name", "kind", "default", "annotation", "source", "context")
)


class FuncSig(IDCache):
    """ Wrapper around sigtools signature gathering """

    _cache = Cache()
    EMPTY = _empty

    _KIND_MAP = {
        "POSITIONAL_ONLY": Kind.POSITIONAL,
        "KEYWORD_ONLY": Kind.KEYWORD,
        "POSITIONAL_OR_KEYWORD": Kind.POSITIONAL | Kind.KEYWORD,
        "VAR_POSITIONAL": Kind.POSITIONAL | Kind.VARIADIC,
        "VAR_KEYWORD": Kind.KEYWORD | Kind.VARIADIC,
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
        except TypeError as err:  # Can this be prevented?
            LOG.debug("Error getting signature for {}".format(self._func))
            LOG.debug(traceback.format_exc())
        except RuntimeError as err:  # https://github.com/epsy/sigtools/issues/10
            LOG.debug("Error getting signature for {}".format(self._func))
        finally:
            if restore_attr:
                self._func.__annotations__ = restore_val

    def _get_parameters(self):
        if not self._sig:
            return

        source = sorted(self._sig.sources["+depths"].items(), key=lambda x: x[1])[-1][0]

        self._returns = FuncSigArg(
            "",
            None,
            self.EMPTY,
            self._sig.return_annotation,
            source,
            getattr(source, "__globals__", {}),
        )

        self._parameters = collections.OrderedDict()  # type: Dict[str, FuncSigArg]
        for name, param in self._sig.parameters.items():
            source = (self._sig.sources.get(name) or [self._returns.source])[0]
            self._parameters[name] = FuncSigArg(
                name,
                self._KIND_MAP[str(param.kind)]
                | (0 if param.default is self.EMPTY else Kind.DEFAULT),
                param.default,
                param.annotation,
                source,
                getattr(source, "__globals__", {}),
            )
