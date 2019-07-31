""" Tools to expose and work with a modules public API """

if False:  # type checking
    from typing import *

__version__ = "0.3.3"

import re as _re
from importlib import import_module as _import_module
from surface._traversal import APITraversal, recurse
from surface._compare import compare, PATCH, MINOR, MAJOR
from surface._type import UNKNOWN
from surface._base import (
    POSITIONAL,
    KEYWORD,
    VARIADIC,
    DEFAULT,
    Var,
    Arg,
    Func,
    Class,
    Module,
    to_dict,
    from_dict,
)


def get_api(
    name, exclude_modules=False, all_filter=True
):  # type: (str, bool, bool) -> Tuple[Any, ...]
    """
        Get a representation of the provided publicly exposed API.

        Args:
            name (str): path to module. eg mymodule.submodule
            exclude_modules (bool): Exclude "naked" imports from API.
            all_filter (bool): Filter API based on __all__ attribute when present.

        Returns:
            Tuple[Any, ...]: Representation of API
    """
    mod = _import_module(name)
    traversal = APITraversal(exclude_modules=exclude_modules, all_filter=all_filter)
    API = traversal.traverse(mod)
    return tuple(API)


def format_api(api, colour=False, indent=""):  # type: (Iterable[Any], bool, str) -> str
    """ Format api into an easier to read representation """
    result = ""
    magenta = ("\033[35m{}\033[0m" if colour else "{}").format
    cyan = ("\033[36m{}\033[0m" if colour else "{}").format
    green = ("\033[32m{}\033[0m" if colour else "{}").format
    for item in api:
        if isinstance(item, (Class, Module)):
            result += indent + "{} {}:\n".format(
                magenta(item.__class__.__name__.lower()), cyan(item.name)
            )
            if item.body:
                result += format_api(item.body, colour, indent + "    ")
        elif isinstance(item, Func):
            if item.args:
                result += indent + "{} {}(\n".format(magenta("def"), cyan(item.name))
                result += format_api(item.args, colour, indent + "    ")
                result += indent + "): -> {}\n".format(green(item.returns))
            else:
                result += indent + "{} {}(): -> {}\n".format(
                    magenta("def"), cyan(item.name), green(item.returns)
                )
        elif isinstance(item, Arg):
            name = item.name
            if item.kind & VARIADIC:
                name = "*" + name
                if item.kind & KEYWORD:
                    name = "*" + name
            result += indent + "{}: {}\n".format(name, green(item.type))
        elif isinstance(item, Var):
            result += indent + "{}: {}\n".format(item.name, green(item.type))
        else:
            result += indent + str(item) + "\n"
    return result


def bump_semantic_version(level, version):  # type: (str, str) -> str
    """ Bump version with the provided level """
    parts = _re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not parts:
        raise TypeError("Not a valid semantic version: {}".format(version))
    if level == MAJOR:
        return "{}.0.0".format(int(parts.group(1)) + 1)
    if level == MINOR:
        return "{}.{}.0".format(parts.group(1), int(parts.group(2)) + 1)
    if level == PATCH:
        return "{}.{}.{}".format(
            parts.group(1), parts.group(2), int(parts.group(3)) + 1
        )
    raise ValueError("Unknown level {}".format(level))
