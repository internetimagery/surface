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
from surface._utils import FuncSig, Cache, IDCache

LOG = logging.getLogger(__name__)


type_comment_reg = re.compile(r"# +type: ([\w ,\[\]\.]+)")
type_comment_sig_reg = re.compile(r"# +type: \(([\w ,\[\]\.]*)\) +-> +([\w ,\[\]\.]+)")
type_attr_reg = re.compile(
    r"(?:^|(?<=[, \[]))(?:typing\.)?({})\b".format("|".join(TYPING_ATTRS))
)

_cache_type = Cache(500)


# Collect types as before. normalizing the type to its defined module (as this what annotations do too)
# make a collection of "exports" from modules / classes. eg things not defined within the module itself
# use this collection to map onto a type, to move exposed types into the public module

# TODO: since strings can be treated as annotations. Treat comment and docstring types as annotations too!
# then annotation logic just has to figure out what to do.

# TODO: clean this all up.
# TODO: Use Items as entry points.

# TODO: Maybe come back to this. Just use existing messy typing logic at the moment.
# TODO: clean things up with new nody style traversal
# TODO: THEN tackle new typing, and new module-first traversal.


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
        self.params = collections.OrderedDict()
        for name, param in sig.parameters.items():
            if param.annotation is not FuncSig.EMPTY:
                self.params[name] = handle_live_annotation(param.annotation)
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
                    self.params[name] = get_live_type(param.default)
                continue
            self.params[name] = UNKNOWN

    def _map_returns(self, sig):
        if sig.returns.annotation is not FuncSig.EMPTY:
            self.returns = handle_live_annotation(sig.returns.annotation)
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


#########################
# Clean this mess up
#########################


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

    if inspect.isfunction(value):
        func_type = FuncType(value)
        cache_value = func_type.as_var()
    else:
        cache_value = (
            get_comment_type(value, name, parent)
            or get_annotate_type(value, name, parent)
            or get_live_type(value)
        )
    _cache_type[value_id] = cache_value
    return cache_value


def get_comment_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    return None


def get_annotate_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    if inspect.isclass(parent) or inspect.ismodule(parent):
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
        func_type = FuncType(value)
        return func_type.as_var()
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
