""" Tools to expose and work with a modules public API """

if False:  # type checking
    from typing import *

__version__ = "0.8.0"

import re as _re
import importlib as _importlib
from surface._traversal import Traversal, recurse
from surface._compare import Changes, SemVer, RULES
from surface._base import Kind, API, UNKNOWN


def get_api(
    name, exclude_modules=False, all_filter=False, depth=6
):  # type: (str, bool, bool, int) -> API.Module
    """
        Get a representation of the provided publicly exposed API.

        Args:
            name (str): path to module. eg mymodule.submodule
            exclude_modules (bool): Exclude "naked" imports from API.
            all_filter (bool): Filter API based on __all__ attribute when present.
            depth (int): Limit how far to spider out into the modules.

        Returns:
            Tuple[API.Module, ...]: Representation of API
    """
    mod = _importlib.import_module(name)
    traversal = Traversal(
        exclude_modules=exclude_modules, all_filter=all_filter, depth=depth
    )
    api = traversal.traverse(mod)
    return api


def format_api(api, colour=False, indent=""):  # type: (Iterable[Any], bool, str) -> str
    """ Format api into an easier to read representation """
    result = ""
    yellow = ("\033[33m{}\033[0m" if colour else "{}").format
    magenta = ("\033[35m{}\033[0m" if colour else "{}").format
    cyan = ("\033[36m{}\033[0m" if colour else "{}").format
    green = ("\033[32m{}\033[0m" if colour else "{}").format
    for item in api:
        if isinstance(item, (API.Class, API.Module)):
            result += indent + "{} {}:\n".format(
                magenta(item.__class__.__name__.lower()), cyan(item.name)
            )
            if item.body:
                result += format_api(item.body, colour, indent + "    ")
        elif isinstance(item, API.Func):
            if item.args:
                result += indent + "{} {}(\n".format(magenta("def"), cyan(item.name))
                result += format_api(item.args, colour, indent + "    ")
                result += indent + "): -> {}\n".format(green(item.returns))
            else:
                result += indent + "{} {}(): -> {}\n".format(
                    magenta("def"), cyan(item.name), green(item.returns)
                )
        elif isinstance(item, API.Arg):
            name = item.name
            if item.kind & Kind.VARIADIC:
                name = "*" + name
                if item.kind & Kind.KEYWORD:
                    name = "*" + name
            result += indent + "{}: {}\n".format(name, green(item.type))
        elif isinstance(item, API.Var):
            result += indent + "{}: {}\n".format(item.name, green(item.type))
        elif isinstance(item, API.Unknown):
            result += indent + "{}? {}: {}\n".format(
                item.name, yellow(item.type), yellow(item.info)
            )
        else:
            result += indent + str(item) + "\n"
    return result


def bump_semantic_version(level, version):  # type: (str, str) -> str
    """ Bump version with the provided level """
    parts = _re.match(r"(\d+)(?:\.(\d+)(?:\.(\d+)|$)|$)", version)
    if not parts:
        raise ValueError("Not a valid semantic version: {}".format(version))
    if level not in (SemVer.PATCH, SemVer.MINOR, SemVer.MAJOR):
        raise ValueError("Invalid level {}".format(level))

    major = int(parts.group(1))
    minor = int(parts.group(2) or 0)
    patch = int(parts.group(3) or 0)

    if level == SemVer.PATCH:
        patch += 1
    elif level == SemVer.MINOR or (level == SemVer.MAJOR and major == 0):
        minor += 1
        patch = 0
    elif level == SemVer.MAJOR:
        major += 1
        minor = patch = 0
    return "{}.{}.{}".format(major, minor, patch)
