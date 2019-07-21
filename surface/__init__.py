import re
from surface._traversal import traverse, recurse
from surface._compare import compare, PATCH, MINOR, MAJOR
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
)

if False:  # Type checking
    from typing import Tuple, Iterable, Any


def get_api(name):  # type: (str) -> Tuple[Any, ...]
    """
        Get a representation of the provided publicly exposed API.

        Args:
            name (str): path to module. eg mymodule.submodule

        Returns:
            Tuple[Any, ...]: Representation of API
    """
    mod = __import__(name, fromlist=[""])
    API = traverse(mod)
    return tuple(API)


def format_api(api, indent=""):  # type: (Iterable[Any], str) -> str
    """ Format api into an easier to read representation """
    result = ""
    for item in api:
        if isinstance(item, (Class, Module)):
            result += indent + "{} {}:\n".format(
                item.__class__.__name__.lower(), item.name
            )
            if item.body:
                result += format_api(item.body, indent + "    ")
        elif isinstance(item, Func):
            if item.args:
                result += indent + "def {}(\n".format(item.name)
                result += format_api(item.args, indent + "    ")
                result += indent + "): -> {}\n".format(item.returns)
            else:
                result += indent + "def {}(): -> {}\n".format(item.name, item.returns)
        elif isinstance(item, Arg):
            name = ("*" if item.kind & VARIADIC else "") + item.name
            result += indent + "{}: {}\n".format(name, item.type)
        elif isinstance(item, Var):
            result += indent + "{}: {}\n".format(item.name, item.type)
        else:
            result += indent + str(item) + "\n"
    return result


def bump_semantic_version(level, version):  # type: (str, str) -> str
    """ Bump version with the provided level """
    parts = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
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
