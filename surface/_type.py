""" Colllect typing info """

if False:  # type checking
    from typing import *


import re
import ast
import types
import token
import typing
import logging
import inspect
import traceback
import itertools
import importlib
import collections

from surface._base import UNKNOWN, PY2, TYPE_CHARS
from surface._doc import parse_docstring
from surface._comment import get_comment
from surface._utils import FuncSig, Cache, IDCache, get_tokens
from surface._item_static import (
    ModuleAst,
    NameAst,
    TupleAst,
    UnknownAst,
    SliceAst,
    EllipsisAst,
)

if PY2:
    import __builtin__ as builtins
else:
    import builtins

LOG = logging.getLogger(__name__)

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
        for name, param in sig.parameters.items():
            context = Context(param.context)
            if param.annotation is not FuncSig.EMPTY:
                self.params[name] = AnnotationType(param.annotation, context).type
                continue
            comment_types = get_comment(param.source)
            if comment_types:
                self.params[name] = AnnotationType(
                    comment_types[0].get(name, UNKNOWN), context
                ).type
                continue
            docstring_types = parse_docstring(param.source)
            if docstring_types:
                self.params[name] = AnnotationType(
                    docstring_types[0].get(name, UNKNOWN), context
                ).type
                continue
            # If we have nothing else to go on, check for a default value
            if param.default is not FuncSig.EMPTY:
                if param.default is None:
                    # Value is optional
                    self.params[name] = "typing.Union[NoneType, {}]".format(UNKNOWN)
                else:
                    self.params[name] = str(LiveType(param.default))
                continue
            self.params[name] = UNKNOWN

    def _map_returns(self, sig):
        context = Context(sig.returns.context)
        if sig.returns.annotation is not FuncSig.EMPTY:
            self.returns = AnnotationType(sig.returns.annotation, context).type
            return
        comment_types = get_comment(sig.returns.source)
        if comment_types:
            self.returns = AnnotationType(comment_types[1], context).type
            return
        docstring_types = parse_docstring(sig.returns.source)
        if docstring_types:
            self.returns = AnnotationType(docstring_types[1], context).type
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
        func_type = FuncType(prop.fget)
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
        obj_type = type(obj)
        if obj_type == type(None):
            return "NoneType"
        for builtin_type in BUILTIN_TYPES:
            if obj is builtin_type:
                return obj.__name__
            if obj_type is builtin_type:
                return obj_type.__name__
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


class Context(IDCache):
    """ Clone and customize a provided context """

    def __init__(self, context):  # type: (Dict[str, Any]) -> None
        # Injecting typing into the context for convenience
        self.context = typing.__dict__.copy()
        self.context["typing"] = typing
        self.context.update(context)


class AnnotationType(object):

    type_visitors = (ModuleAst, NameAst, TupleAst, SliceAst, UnknownAst, EllipsisAst)

    def __init__(self, obj, context):  # type: (Any, Context) -> None
        self._context = context
        self.type = self._get_type(obj)
        self.type = self._sort_union(self.type)

    def _get_type(self, obj):  # type: (Any) -> str
        if isinstance(obj, basestring if PY2 else str):  # type: ignore
            # In unknown exists, then we would have crafted the type ourselves, pass it on.
            if UNKNOWN in obj:
                return obj
            try:
                # If it is a string, treat as forward reference.
                obj = self._eval_type(obj)
            except Exception:
                # If something failed there is something wrong with the type.
                LOG.debug(traceback.format_exc())
                return UNKNOWN
        return (
            self._handle_none(obj)
            or self._handle_typing(obj)
            or self._handle_builtin(obj)
            or self._handle_class(obj)
            or self._handle_function(obj)
            or UNKNOWN
        )

    @staticmethod
    def _handle_none(obj):
        if obj is None:
            return "NoneType"
        return None

    @staticmethod
    def _handle_typing(obj):
        if isinstance(obj, typing.TypingMeta) or isinstance(
            type(obj), typing.TypingMeta
        ):
            return str(obj)
        return None

    @staticmethod
    def _handle_builtin(obj):
        for builtin_type in BUILTIN_TYPES:
            if obj is builtin_type:
                return obj.__name__
        return None

    @staticmethod
    def _handle_class(obj):
        if not inspect.isclass(obj):
            return None
        name = getattr(obj, "__name__", UNKNOWN)
        module = getattr(inspect.getmodule(obj), "__name__", "")
        if module:
            return "{}.{}".format(module, name)
        return name

    @staticmethod
    def _handle_function(obj):
        if not inspect.isfunction(obj) and not inspect.ismethod(obj):
            return None
        func = FuncType(obj)
        return func.as_var()

    def _sort_union(self, type_string):
        if "typing.Union" not in type_string:
            return type_string
        tokens = get_tokens(type_string)
        num_tokens = len(tokens) - 1
        replace = []
        i = 1
        while i < num_tokens:
            i += 1
            if not (
                tokens[i][0] == token.NAME
                and tokens[i][1] == "Union"
                and tokens[i - 2][1] == "typing"
            ):
                continue
            start = tokens[i + 2][2][1]  # First token inside braces
            entries = []
            marker = 0
            brace = 0
            while i < num_tokens:
                i += 1
                sub_tok = tokens[i]
                if sub_tok[0] != token.OP:
                    continue

                if sub_tok[1] == "[":
                    brace += 1
                elif sub_tok[1] == "]":
                    brace -= 1

                if brace > 1:
                    continue

                if sub_tok[1] in "],":
                    sub_type_string = type_string[marker : tokens[i - 1][3][1]]
                    entries.append(self._sort_union(sub_type_string).strip())
                if sub_tok[1] in "[,":
                    marker = tokens[i + 1][2][1]

                if not brace:
                    break
            end = tokens[i - 1][3][1]  # Last token inside braces
            entries.sort()  # HERE! Sort those internals
            replace.append((start, end, ", ".join(entries)))

        for rep in sorted(replace, reverse=True):
            type_string = type_string[: rep[0]] + rep[2] + type_string[rep[1] :]
        return type_string

    def _eval_type(self, type_string):
        try:
            # Just try running it first. We might be lucky!
            return eval(type_string, self._context.context)
        except (NameError, AttributeError):
            # Retry the evaluation with an updated context
            self._include_imports(type_string)
            try:
                return eval(type_string, self._context.context)
            except (NameError, AttributeError) as err:
                LOG.warning("Error in typing: {}".format(err))
                raise
        except SyntaxError as err:
            LOG.warning("Invalid syntax in type '{}'".format(type_string))
            raise

    def _include_imports(self, type_string):
        # Something failed. First add imports to the context. Docstrings need full paths sometimes.
        stack = [ModuleAst.parse(self.type_visitors, type_string)]
        while stack:
            item = stack.pop()
            stack.extend(item.values())
            if not isinstance(item, NameAst):
                continue
            parts = item.name.split(".")
            if len(parts) < 2:
                continue
            for i in range(len(parts) - 1):
                path = ".".join(parts[: i + 1])
                if path in self._context.context:
                    continue
                try:
                    self._context.context[path] = importlib.import_module(path)
                except ImportError:
                    pass
