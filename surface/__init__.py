import re
from importlib import import_module
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


def get_api(name, exclude_modules=False):  # type: (str, bool) -> Tuple[Any, ...]
    """
        Get a representation of the provided publicly exposed API.

        Args:
            name (str): path to module. eg mymodule.submodule
            exclude_modules (bool): Exclude "naked" imports from API.

        Returns:
            Tuple[Any, ...]: Representation of API
    """
    mod = import_module(name)
    API = traverse(mod, exclude_modules)
    return tuple(API)


def format_api(api, colour=True, indent=""):  # type: (Iterable[Any], bool, str) -> str
    """ Format api into an easier to read representation """
    result = ""
    magenta = "\033[35m{}\033[0m" if colour else "{}"
    cyan = "\033[36m{}\033[0m" if colour else "{}"
    green = "\033[32m{}\033[0m" if colour else "{}"
    for item in api:
        if isinstance(item, (Class, Module)):
            result += indent + "{} {}:\n".format(
                magenta.format(item.__class__.__name__.lower()), cyan.format(item.name)
            )
            if item.body:
                result += format_api(item.body, colour, indent + "    ")
        elif isinstance(item, Func):
            if item.args:
                result += indent + "{} {}(\n".format(
                    magenta.format("def"), cyan.format(item.name)
                )
                result += format_api(item.args, colour, indent + "    ")
                result += indent + "): -> {}\n".format(green.format(item.returns))
            else:
                result += indent + "{} {}(): -> {}\n".format(
                    magenta.format("def"),
                    cyan.format(item.name),
                    green.format(item.returns),
                )
        elif isinstance(item, Arg):
            name = ("*" if item.kind & VARIADIC else "") + item.name
            result += indent + "{}: {}\n".format(name, green.format(item.type))
        elif isinstance(item, Var):
            result += indent + "{}: {}\n".format(item.name, green.format(item.type))
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
