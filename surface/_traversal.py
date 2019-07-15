""" Traverse an API heirarchy """


# TODO: import module by name
# TODO: get its global name, and path
# TODO: cache path names to module name for efficiency

# TODO: walk through everything it exposes at the top level
# TODO: eg: names not starting with underscores
# TODO: or anything in the __all__ variable.

# TODO: create a simplified representation of the signatures found (names and types)

# BONUS: collect type information as part of the signatures
# BONUS: traverse heirarchy for specified types, recursively getting their api
# BONUS: so later a type can be compared by value, not just name

import ast
import typing
import inspect
import sigtools
from surface._base import *


def traverse(obj): # type: (Any) -> List[Any]
    """ Entry point to generating an API representation. """
    attributes = (
        attr
        for attr in inspect.getmembers(obj)
        if is_public(attr[0])
    )
    # __all__ attribute restricts import with *,
    # and displays what is intended to be public
    whitelist = getattr(obj, "__all__", [])
    if whitelist:
        attributes = (attr for attr in attributes if attr[0] in whitelist)

    # Sort the attributes by name for readability, and diff-ability (is that a word?)
    attributes = sorted(attributes, key=lambda a: a[0])

    # Walk the surface of the object, and extract the information
    for name, value in attributes:
        # TODO: How to ensure we find the original classes and methods, and not wrappers?

        if inspect.isclass(value):
            yield handle_class(name, value)
        # Python2
        elif inspect.ismethod(value):
            yield handle_method(name, value)
        elif inspect.isfunction(value):
            # python3
            if inspect.isclass(obj):
                yield handle_method(name, value)
            else:
                yield handle_function(name, value)
        elif name != "__init__":
            yield handle_variable(name, value)


def handle_function(name, value):
    sig = sigtools.signature(value)
    return Func(
        name,
        tuple(
            Arg(
                n,
                typing.Any,
                convert_arg_kind(str(p.kind)) | (0 if p.default is sig.empty else DEFAULT),
            )
            for n, p in sig.parameters.items()
        ),
        typing.Any,
    )


def handle_method(name, value):
    sig = sigtools.signature(value)
    params = list(sig.parameters.items())
    if not "@staticmethod" in inspect.getsource(value):
        params = params[1:]
    return Func(
        name,
        tuple(
            Arg(
                n,
                typing.Any,
                convert_arg_kind(str(p.kind)) | (0 if p.default is sig.empty else DEFAULT),
            )
            for n, p in params
        ),
        typing.Any,
    )


def handle_class(name, value):
    return Class(name, tuple(traverse(value)))


def handle_variable(name, value):
    # TODO: Handle typing of value
    return Var(name, typing.Any)


def is_public(name):
    return name == "__init__" or not name.startswith("_")


def convert_arg_kind(kind):
    if kind == "POSITIONAL_ONLY":
        return POSITIONAL
    if kind == "KEYWORD_ONLY":
        return KEYWORD
    if kind == "POSITIONAL_OR_KEYWORD":
        return POSITIONAL | KEYWORD
    if kind == "VAR_POSITIONAL":
        return POSITIONAL | VARIADIC
    if kind == "VAR_KEYWORD":
        return KEYWORD | VARIADIC
    raise TypeError("Unknown type.")
