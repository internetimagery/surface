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
from surface._utils import FuncSig, Cache

LOG = logging.getLogger(__name__)


__all__ = ["get_type", "get_type_func"]

type_comment_reg = re.compile(r"# +type: ([\w ,\[\]\.]+)")
type_comment_sig_reg = re.compile(r"# +type: \(([\w ,\[\]\.]*)\) +-> +([\w ,\[\]\.]+)")
type_attr_reg = re.compile(
    r"(?:^|(?<=[, \[]))(?:typing\.)?({})\b".format("|".join(TYPING_ATTRS))
)

_cache_type = Cache(500)
_cache_func_type = Cache(500)


# Collect types as before. normalizing the type to its defined module (as this what annotations do too)
# make a collection of "exports" from modules / classes. eg things not defined within the module itself
# use this collection to map onto a type, to move exposed types into the public module


class FuncType(object):
    """ Collect types on function objects """

    _cache = Cache()

    def __new__(cls, func):
        func_id = id(func)
        cache_item = cls._cache.get(func_id, None)
        if cache_item is None:
            cls._cache[func_id] = cache_item = super(FuncType, cls).__new__(cls)
        return cache_item

    def __init__(self, func):
        self._func = func
        self._params = {}
        self._return_type = UNKNOWN


# TODO: clean this all up.
# TODO: Use Items as entry points.

# TODO: Maybe come back to this. Just use existing messy typing logic at the moment.
# TODO: clean things up with new nody style traversal
# TODO: THEN tackle new typing, and new module-first traversal.


class TypeCollector(object):
    """ Collect types on behalf of Item objects """

    _cache_func_type = Cache(500)

    def get_type_func(self, item):  # type: (FunctionItem) -> Tuple[Dict[str, str], str]
        item_id = id(item.item)
        cache_value = self._cache_func_type.get(item_id, None)
        if cache_value is None:
            self._cache_func_type[item_id] = cache_value = (
                get_comment_type_func(item.item)
                or get_docstring_type_func(item.item)
                or get_annotate_type_func(item.item, item.name)
            )
        return cache_value


def format_annotation(ann):  # type: (Any) -> str
    if PY2:  # Annotations do not exist in python 2
        return UNKNOWN

    if isinstance(ann, str):
        # TODO: Use existing static logic?
        # TODO: Or do this check outside this function?
        return UNKNOWN

    if inspect.isclass(ann):
        if ann.__module__ == "typing":
            return str(ann)
        if ann.__module__ == "builtins":
            return ann.__name__
        return "{}.{}".format(ann.__module__, ann.__qualname__)

    return UNKNOWN


# TODO: handle types in here...
# TODO: function typer, return ordered dict, name / type
# TODO: and return type
# TODO: else a standard type, return string... which is mostly the case now.

# TODO: similar can_handle methodology


# def get_type(scope): # type: (Object) -> str
#     obj_id = id(scope.obj)
#     if obj_id in _cache_type:
#         return _cache_type[obj_id]
#
#     scope_type = type(scope)
#     if scope_type == Object:
#         _cache_type[obj_id] = get_live_type(scope.obj)
#
#     return _cache_type.get(obj_id, UNKNOWN)


def get_type(value, name="", parent=None):  # type: (Any, str, Any) -> str
    value_id = id(value)
    cache_value = _cache_type.get(value_id, None)
    if cache_value is not None:
        return cache_value

    cache_value = (
        get_comment_type(value, name, parent)
        or get_annotate_type(value, name, parent)
        or get_live_type(value)
    )
    _cache_type[value_id] = cache_value
    return cache_value


def get_type_func(
    value, name="", parent=None
):  # type: (Any, str, Any) -> Tuple[Dict[str, str], str]
    value_id = id(value)
    cache_value = _cache_func_type.get(value_id, None)
    if cache_value is not None:
        return cache_value

    cache_value = (
        get_comment_type_func(value)
        or get_docstring_type_func(value)
        or get_annotate_type_func(value, name)
    )
    _cache_func_type[value_id] = cache_value
    return cache_value


def get_comment_type_func(value):  # type: (Any) -> Optional[Tuple[Dict[str, str], str]]
    sig = FuncSig(value)
    if not sig:
        return None

    base_typing = get_comment(sig.returns.source)
    if not base_typing:
        return None
    return_type = base_typing[1]

    # map params from each function to attributes.
    params = collections.OrderedDict()  # type: Dict[str, str]
    for name, param in sig.parameters.items():
        source_type = get_comment(param.source)
        if source_type:
            params[param] = source_type[0].get(param, UNKNOWN)
        else:
            params[param] = UNKNOWN
    return params, return_type


def get_docstring_type_func(
    value
):  # type: (Any) -> Optional[Tuple[Dict[str, str], str]]
    sig = FuncSig(value)
    if not sig:
        return None

    base_typing = get_comment(sig.returns.source)
    if not base_typing:
        return None
    return_type = base_typing[1]

    # map params from each function to attributes.
    params = collections.OrderedDict()  # type: Dict[str, str]
    for name, param in sig.parameters.items():
        source_type = parse_docstring(param.source)  # Just grabbing one for now
        if source_type:
            params[param] = source_type[0].get(param, UNKNOWN)
        else:
            params[param] = UNKNOWN
    return params, return_type


def get_annotate_type_func(
    value, name
):  # type: (Any, str) -> Tuple[Dict[str, str], str]
    sig = FuncSig(value)
    if not sig:
        return {}, UNKNOWN

    return_type = (
        handle_live_annotation(sig.returns.annotation)
        if sig.returns.annotation is not FuncSig.EMPTY
        else UNKNOWN
    )

    # map params from each function to attributes.
    params = collections.OrderedDict()  # type: Dict[str, str]
    for name, param in sig.parameters.items():
        if param.annotation is not FuncSig.EMPTY:
            # If we are given an annotation, use it
            params[name] = handle_live_annotation(param.annotation)
        elif param.default is not FuncSig.EMPTY:
            # If we have a default value, use that type
            if param.default is None:
                # Value is optional
                params[name] = "typing.Optional[{}]".format(UNKNOWN)
            else:
                params[name] = get_live_type(param.default)
        else:
            params[name] = UNKNOWN
    return params, return_type


def get_docstring_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    if inspect.isfunction(value):
        result = get_docstring_type_func(value)
        if result:
            params, return_type = result
            return "typing.Callable[{}, {}]".format(
                "[{}]".format(", ".join(p for p in params.values()))
                if params
                else "...",
                return_type,
            )
    return None


def get_comment_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    if inspect.isfunction(value):
        result = get_comment_type_func(value)
        if result:
            params, return_type = result
            return "typing.Callable[{}, {}]".format(
                "[{}]".format(", ".join(params.values())) if params else "...",
                return_type,
            )
    return None


def get_annotate_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    if type(value) == types.FunctionType:
        params, return_type = get_annotate_type_func(value, name)
        return "typing.Callable[{}, {}]".format(
            "[{}]".format(", ".join(params.values())) if params else "...", return_type
        )
    elif inspect.isclass(parent) or inspect.ismodule(parent):
        annotation = getattr(parent, "__annotations__", {})
        if name in annotation:
            return handle_live_annotation(annotation[name])
    return None


def get_live_type(value):  # type: (Any) -> str
    # Standard types
    value_type = type(value)
    return (
        handle_live_standard_type(value_type)
        or handle_live_container_type(value, value_type)
        or handle_live_abstract(value, value_type)
        or UNKNOWN
    )


def handle_live_standard_type(value_type):  # type: (Any) -> Optional[str]
    # Numeric
    if value_type == int:
        return "int"
    if value_type == float:
        return "float"
    if value_type == complex:
        return "complex"

    # Strings
    if value_type == str:
        return "str"
    try:  # python 2
        if value_type == unicode:  # type: ignore
            return "unicode"
    except NameError:
        pass

    # Aaaaaand the rest
    if value_type == bool:
        return "bool"
    if value_type == type(None):
        return "None"

    return None


def handle_live_container_type(value, value_type):  # type: (Any, Any) -> Optional[str]
    # Sequences
    if value_type == list:
        return "typing.List[{}]".format(get_live_type(value[0]) if value else UNKNOWN)
    if value_type == tuple:
        internals = [get_live_type(item) for item in value]
        if not internals:
            internals = ["{}, ...".format(UNKNOWN)]
        return "typing.Tuple[{}]".format(", ".join(internals))

    # Hashies!
    if value_type == set:
        template = "typing.Set[{}]"
        for item in value:
            return template.format(get_live_type(item))
        return template.format(UNKNOWN)
    if value_type == dict:
        template = "typing.Dict[{}, {}]"
        for k, v in value.items():
            return template.format(get_live_type(k), get_live_type(v))
        return template.format(UNKNOWN, UNKNOWN)

    # Generators
    # IMPORTANT!
    #     Taking an item out of the generator here to get the type is fine for cli usage.
    #     But if used during a live session this would be an problem.
    if value_type == types.GeneratorType:
        # NOTE: Generator return value can be taken from StopIteration return value if needed.
        template = "typing.Iterable[{}]"
        for item in value:
            return template.format(get_live_type(item))
        return template.format(UNKNOWN)
    # TODO: handle types.AsyncGeneratorType

    return None


def handle_live_abstract(value, value_type):  # type: (Any, Any) -> Optional[str]
    if value_type == types.FunctionType:
        params, return_type = get_type_func(value)
        return "typing.Callable[{}, {}]".format(
            "[{}]".format(", ".join(params.values())) if params else "...", return_type
        )

    return None


# Python3 function
def handle_live_annotation(value):  # type: (Any) -> str
    import typing

    if type(value) == typing.GenericMeta:
        return str(value)
    if inspect.isclass(value):
        if value.__module__ == "builtins":
            return value.__name__
        return "{}.{}".format(value.__module__, value.__name__)
    if type(value) == types.FunctionType:
        return get_live_type(value)
    return UNKNOWN


# This is a bit of a brute force way of ensuring typing declarations are abspath.
# It does not take into account locally overidding names in typing module
# It is also not making arbitrary types absolute.
# Could be improved with a lot of static parsing, but for now this should be ok!
def normalize(type_string):  # type: (str) -> str
    return type_attr_reg.sub(r"typing.\1", type_string)
