""" Colllect typing info """

if False:  # type checking
    from typing import *


import re
import ast
import types
import token
import logging
import inspect
import traceback
import itertools
import collections

from surface._base import UNKNOWN, PY2, TYPING_ATTRS
from surface._doc import parse_docstring
from surface._comment import get_comment
from surface._utils import FuncSig, Cache, IDCache, abs_type

if PY2:
    import __builtin__ as builtins
else:
    import builtins

BUILTIN_TYPES = tuple(b for b in builtins.__dict__.values() if isinstance(b, type))


class FuncType(IDCache):
    """ Collect typing information on a function """

    _cache = Cache()

    def __init__(self, func):
        self.params = collections.OrderedDict()
        self.returns = UNKNOWN

        sig = FuncSig(func)
        if sig:
            self._map_params(sig)
            self._map_returns(sig)

    def as_var(self):
        params = (
            "[{}]".format(", ".join(self.params.values())) if self.params else "..."
        )
        return "typing.Callable[{}, {}]".format(params, self.returns)

    def _map_params(self, sig):
        """ Check annotations first, then type comments, then docstrings """
        context = sig.context
        self.params = collections.OrderedDict()
        for name, param in sig.parameters.items():
            if param.annotation is not FuncSig.EMPTY:
                self.params[name] = str(AnnotationType(param.annotation, context))
                continue
            comment_types = get_comment(param.source)
            if comment_types:
                self.params[name] = comment_types[0].get(name, UNKNOWN)
                continue
            docstring_types = parse_docstring(param.source)
            if docstring_types:
                self.params[name] = docstring_types[0].get(name, UNKNOWN)
                continue
            # If we have nothing else to go on, check for a default value
            if param.default is not FuncSig.EMPTY:
                if param.default is None:
                    # Value is optional
                    self.params[name] = "typing.Optional[{}]".format(UNKNOWN)
                else:
                    self.params[name] = str(LiveType(param.default))
                continue
            self.params[name] = UNKNOWN

    def _map_returns(self, sig):
        if sig.returns.annotation is not FuncSig.EMPTY:
            self.returns = str(AnnotationType(sig.returns.annotation, sig.context))
            return
        comment_types = get_comment(sig.returns.source)
        if comment_types:
            self.returns = comment_types[1]
            return
        docstring_types = parse_docstring(sig.returns.source)
        if docstring_types:
            self.returns = docstring_types[1]
            return
        self.returns = UNKNOWN


class LiveType(IDCache):
    """ Get string representation of some object type """

    _cache = Cache()

    def __init__(self, obj):  # type: (Any) -> None
        self._type = self._get_type(obj)

    def __str__(self):
        return self._type

    def _get_type(self, obj):  # type: (Any) -> str
        return (
            self._handle_container(obj)
            or self._handle_function(obj)
            or self._handle_property(obj)
            or self._handle_descriptor(obj)
            or self._handle_builtin(obj)
            or self._handle_class(obj)
            or UNKNOWN
        )

    @staticmethod
    def _handle_descriptor(desc):
        if not inspect.isdatadescriptor(desc) and not inspect.ismethoddescriptor(desc):
            return None
        func_type = FuncType(desc.__get__)
        return func_type.returns

    @staticmethod
    def _handle_property(prop):
        if not isinstance(prop, property):
            return None
        func_type = FuncType(prop.getter)
        return func_type.returns

    @staticmethod
    def _handle_function(func):
        if not inspect.isfunction(func) and not inspect.ismethod(func):
            return None

        func_type = FuncType(func)
        return func_type.as_var()

    @staticmethod
    def _handle_class(obj):
        if not inspect.isclass(obj):
            return None
        module = getattr(inspect.getmodule(obj), "__name__", "")
        name = getattr(obj, "__qualname__", "") or getattr(obj, "__name__", "")
        if not name:
            return None
        if not module:
            return name
        return "{}.{}".format(module, name)

    @staticmethod
    def _handle_builtin(obj):
        if type(obj) == type(None):
            return "None"
        if obj in BUILTIN_TYPES:
            return obj.__name__
        if isinstance(obj, BUILTIN_TYPES):
            return type(obj).__name__
        return None

    def _handle_container(self, obj):
        obj_type = type(obj)

        # Sequences
        if obj_type == list:
            return "typing.List[{}]".format(LiveType(obj[0]) if obj else UNKNOWN)
        if obj_type == tuple:
            internals = [str(LiveType(item)) for item in obj]
            if not internals:
                internals = ["{}, ...".format(UNKNOWN)]
            return "typing.Tuple[{}]".format(", ".join(internals))

        # Hashies!
        if obj_type == set:
            template = "typing.Set[{}]"
            for item in obj:
                return template.format(LiveType(item))
            return template.format(UNKNOWN)
        if obj_type == dict:
            template = "typing.Dict[{}, {}]"
            for k, v in obj.items():
                return template.format(LiveType(k), LiveType(v))
            return template.format(UNKNOWN, UNKNOWN)

        # Generators
        # IMPORTANT!
        #     Taking an item out of the generator here to get the type is fine for cli usage.
        #     But if used during a live session this would be an problem.
        if obj_type == types.GeneratorType:
            # NOTE: Generator return value can be taken from StopIteration return value if needed.
            template = "typing.Iterable[{}]"
            for item in obj:
                return template.format(LiveType(item))
            return template.format(UNKNOWN)
        # TODO: handle types.AsyncGeneratorType

        return None


class AnnotationType(object):
    def __init__(self, obj, context):  # type: (Any, Dict[str, Any]) -> None
        self._type = self._get_type(obj, context)

    def __str__(self):
        return self._type

    def _get_type(self, obj, context):
        return (
            self._handle_str(obj, context)
            or self._handle_type(obj, context)
            or self._handle_builtin(obj, context)
            or self._handle_class(obj, context)
            or self._handle_function(obj, context)
            or UNKNOWN
        )

    @staticmethod
    def _handle_str(obj, context):
        if not isinstance(obj, str):
            return None
        return abs_type(obj, context)

    @staticmethod
    def _handle_type(obj, _):
        if PY2:
            return None

        import typing

        if isinstance(obj, typing.TypingMeta):
            return str(obj)
        return None

    @staticmethod
    def _handle_builtin(obj, _):
        if obj in BUILTIN_TYPES:
            return obj.__name__
        return None

    @staticmethod
    def _handle_class(obj, _):
        if not inspect.isclass(obj):
            return None
        name = getattr(obj, "__name__", UNKNOWN)
        module = getattr(inspect.getmodule(obj), "__name__", "")
        if module:
            return "{}.{}".format(module, name)
        return name

    @staticmethod
    def _handle_function(obj, _):
        if not inspect.isfunction(obj) and not inspect.ismethod(obj):
            return None
        func = FuncType(obj)
        return func.as_var()
