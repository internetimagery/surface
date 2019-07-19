""" Compare two API's """

# TODO: Better formatted output

from surface._base import *

# Semantic types
PATCH = "patch"
MINOR = "minor"
MAJOR = "major"

# Rules:
#     MAJOR:
#         Removing anything
#         Renaming keyword-arguments
#         Adding positional-arguments
#         Changing types (except where types become more generic)
#     MINOR:
#         Adding new variables, functions, classes, modules, optional-keyword-arguments, *args, **kwargs
#         Changing positional-only-argument to include keyword
#         Changing types to be more generic, eg: List[Any] to Sequence[Any]
#     PATCH:
#         Renaming positional-only-arguments
#         Changing nothing


def compare(
    api_old,  # type: Dict[str, Sequence[Any]]
    api_new,  # type: Dict[str, Sequence[Any]]
):  # type: (...) -> List[Change]
    """
        Compare two API's, and return resulting changes.

        patch: version when you make backwards-compatible bug fixes.
        minor: version when you add functionality in a backwards-compatible manner.
        major: version when you make incompatible API changes.
    """
    changes = []
    # Check for renamed modules
    changes.extend(compare_names(api_old, api_new))

    # Check for changes within modules
    for name, new_mod in api_new.items():
        old_mod = api_old.get(name)
        if old_mod:
            changes.extend(compare_deep(old_mod, new_mod))
    return changes


def compare_names(old_names, new_names):
    old_names = set(old_names)
    new_names = set(new_names)
    for name in old_names - new_names:  # Removed
        yield Change(MAJOR, "Removed: {}".format(name))
    for name in new_names - old_names:  # Added
        yield Change(MINOR, "Added: {}".format(name))


def compare_deep(old_item, new_item):
    changes = []
    # Map by name
    old_map = {item.name: item for item in old_item}
    new_map = {item.name: item for item in new_item}

    # Check for renames
    changes.extend(compare_names(old_map, new_map))

    # Check for changes
    for name, new_item in new_map.items():
        old_item = old_map.get(name)
        if not old_item:
            continue
        elif type(old_item) != type(new_item):
            changes.append(Change(MAJOR, "Type Changed: {}".format(name)))
        elif isinstance(new_item, (Class, Module)):
            changes.extend(compare_deep(old_item.body, new_item.body))
        elif isinstance(new_item, Func):
            changes.extend(compare_func(old_item, new_item))
        elif isinstance(new_item, Var):
            if old_item.type != new_item.type:
                changes.append(Change(MAJOR, "Type Changed: {}".format(new_item.type)))
        else:
            raise TypeError("Uknown type {}".format(type(new_item)))

    return changes


def compare_func(old_func, new_func):
    # TODO: specific functionality relating to arguments
    # TODO: split args into positional / keyword
    # TODO: eg: adding *args or **kwargs is minor
    # TODO: removing one of them is major
    # TODO: likewise adding optional keyword args is minor
    # TODO: changing the number of positional arguments is major
    # TODO: renaming position ONLY args is patch
    # TODO: renaming keyword args is major
    return []
