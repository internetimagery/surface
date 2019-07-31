""" Compare two API's """

if False:  # type checking
    from typing import *


import re

try:
    from itertools import zip_longest  # type: ignore
except ImportError:
    from itertools import izip_longest as zip_longest  # type: ignore

from surface._base import *


__all__ = ["PATCH", "MINOR", "MAJOR", "compare"]


# Rules:
#     MAJOR:
#         Removing anything
#         Renaming keyword-arguments
#         Adding positional-arguments
#         Changing types (except where input types become generics)
#     MINOR:
#         Adding new variables, functions, classes, modules, optional-keyword-arguments, *args, **kwargs
#         Changing positional-only-argument to include keyword
#         Changing input types to be generics, eg: List to Sequence, Dict to Mapping etc
#         Unable to verify the change (ie attribute access failed / recursive object)
#     PATCH:
#         Renaming positional-only-arguments
#         Adding new typing information
#         Changing nothing


# Semantic types
PATCH = "patch"
MINOR = "minor"
MAJOR = "major"

# Templates
_was = '{}, Was: "{}", Now: "{}"'.format
_arg = "{}.({})".format


def compare(
    api_old,  # type: Mapping[str, Iterable[Any]]
    api_new,  # type: Mapping[str, Iterable[Any]]
):  # type: (...) -> Set[Change]
    """
        Compare two API's, and return resulting changes.

        patch: version when you make backwards-compatible bug fixes.
        minor: version when you add functionality in a backwards-compatible manner.
        major: version when you make incompatible API changes.
    """
    changes = set()  # type: Set[Change]
    # Check for renamed modules
    changes.update(compare_names("", api_old, api_new))

    # Check for changes within modules
    for name, new_mod in api_new.items():
        old_mod = api_old.get(name)
        if old_mod:
            changes.update(compare_deep(name, old_mod, new_mod))
    return changes


def compare_names(
    basename, old_names, new_names
):  # type: (str, Iterable[str], Iterable[str]) -> Iterable[Change]
    removed = (name for name in old_names if name not in new_names)
    added = (name for name in new_names if name not in old_names)

    for name in removed:  # Removed
        yield Change(MAJOR, "Removed", join(basename, name))
    for name in added:  # Added
        yield Change(MINOR, "Added", join(basename, name))


def compare_deep(
    basename, old_items, new_items
):  # type: (str, Iterable[Any], Iterable[Any]) -> Set[Any]
    changes = set()  # type: Set[Change]
    # Map by name
    old_map = {item.name: item for item in old_items}
    new_map = {item.name: item for item in new_items}

    # Check for renames
    changes.update(compare_names(basename, old_map, new_map))

    # Check for changes
    for name, new_item in new_map.items():
        old_item = old_map.get(name)
        if old_item is None:
            continue
        abs_name = join(basename, name)

        if old_item == new_item:
            continue
        elif isinstance(old_item, Unknown) or isinstance(new_item, Unknown):
            info = old_item.info if isinstance(old_item, Unknown) else new_item.info
            changes.add(
                Change(MINOR, "Could not verify", "{}: {}".format(abs_name, info))
            )
        elif type(old_item) != type(new_item):
            changes.add(
                Change(
                    MAJOR,
                    "Type Changed",
                    _was(abs_name, type(old_item), type(new_item)),
                )
            )
        elif isinstance(new_item, (Class, Module)):
            changes.update(compare_deep(abs_name, old_item.body, new_item.body))
        elif isinstance(new_item, Func):
            changes.update(compare_func(abs_name, old_item, new_item))
        elif isinstance(new_item, Var):
            if old_item.type != new_item.type:
                if old_item.type == UNKNOWN:  # We didn't know the type before.
                    changes.add(Change(PATCH, "Added Type", abs_name))
                else:
                    changes.add(
                        Change(
                            MAJOR,
                            "Type Changed",
                            _was(abs_name, old_item.type, new_item.type),
                        )
                    )
        else:
            raise TypeError("Unknown type: {}".format(type(new_item)))

    return changes


def compare_func(basename, old_func, new_func):  # type: (str, Func, Func) -> Set[Any]
    changes = set()  # type: Set[Change]

    if old_func.returns != new_func.returns:
        level = (
            PATCH
            if old_func.returns == UNKNOWN
            else MINOR
            if is_subtype(old_func.returns, new_func.returns)
            else MAJOR
        )
        changes.add(
            Change(
                level,
                "Return Type Changed",
                _was(basename, old_func.returns, new_func.returns),
            )
        )

    # Check for changes to positional args, where order matters
    old_positional = (arg for arg in old_func.args if arg.kind & POSITIONAL)
    new_positional = (arg for arg in new_func.args if arg.kind & POSITIONAL)
    for old_arg, new_arg in zip_longest(old_positional, new_positional):
        if old_arg == new_arg:
            continue
        elif not old_arg:
            # Adding a new optional arg (ie: arg=None) or variadic (ie *args / **kwargs)
            # is not a breaking change. Adding anything else is.
            level = MINOR if new_arg.kind & (VARIADIC | DEFAULT) else MAJOR
            changes.add(Change(level, "Added Arg", _arg(basename, new_arg.name)))
            continue
        elif not new_arg:
            # Removing an argument is always a breaking change.
            changes.add(Change(MAJOR, "Removed Arg", _arg(basename, old_arg.name)))
            continue

        name = _arg(basename, new_arg.name)
        if old_arg.name != new_arg.name:
            # It's not breaking to rename variadic or positional-only args, but is for anything else
            level = (
                PATCH
                if new_arg.kind == old_arg.kind
                and (new_arg.kind & VARIADIC or new_arg.kind == POSITIONAL)
                else MAJOR
            )
            changes.add(
                Change(level, "Renamed Arg", _was(name, old_arg.name, new_arg.name))
            )
        if is_subtype(old_arg.type, new_arg.type):
            changes.add(
                Change(MINOR, "Type Changed", _was(name, old_arg.type, new_arg.type))
            )
        elif old_arg.type != new_arg.type:
            level = PATCH if old_arg.type == UNKNOWN else MAJOR
            changes.add(
                Change(level, "Type Changed", _was(name, old_arg.type, new_arg.type))
            )
        if old_arg.kind != new_arg.kind:
            # Adding a default to an argument is not a breaking change.
            level = MINOR if new_arg.kind == (old_arg.kind | DEFAULT) else MAJOR
            changes.add(Change(level, "Kind Changed", name))

    # Check for changes to keyword only arguments
    old_keyword = set(
        "({})".format(arg.name) for arg in old_func.args if arg.kind == KEYWORD
    )
    new_keyword = set(
        "({})".format(arg.name) for arg in new_func.args if arg.kind == KEYWORD
    )
    changes.update(compare_names(basename, old_keyword, new_keyword))

    # Finally, check variadic keyword (eg **kwargs)
    old_var_keyword = [
        arg for arg in old_func.args if arg.kind & KEYWORD and arg.kind & VARIADIC
    ]
    new_var_keyword = [
        arg for arg in new_func.args if arg.kind & KEYWORD and arg.kind & VARIADIC
    ]
    if new_var_keyword == old_var_keyword:
        pass
    elif old_var_keyword and not new_var_keyword:
        changes.add(
            Change(MAJOR, "Removed Arg", _arg(basename, old_var_keyword[0].name))
        )
    elif new_var_keyword and not old_var_keyword:
        changes.add(Change(MINOR, "Added Arg", _arg(basename, new_var_keyword[0].name)))
    elif new_var_keyword[0].name != old_var_keyword[0].name:
        changes.add(
            Change(
                PATCH,
                "Renamed Arg",
                _was(
                    _arg(basename, new_var_keyword[0].name),
                    old_var_keyword[0].name,
                    new_var_keyword[0].name,
                ),
            )
        )

    return changes


def join(parent, child):  # type: (str, str) -> str
    return "{}.{}".format(parent, child) if parent else child


# TODO: Flesh this out some more.
# TODO: Probably want to support List Dict etc, as local imports
def is_subtype(subtype, supertype):  # type: (str, str) -> bool
    # Sequences
    match = re.match("typing\.(List|Tuple|MutableSequence)", subtype)
    if match and supertype.startswith("typing.Sequence"):
        return True

    # Mapping
    match = re.match("typing\.(Dict|MutableMapping)", subtype)
    if match and supertype.startswith("typing.Mapping"):
        return True

    return False
