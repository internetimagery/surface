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
):  # type: (...) -> Set[Change]
    """
        Compare two API's, and return resulting changes.

        patch: version when you make backwards-compatible bug fixes.
        minor: version when you add functionality in a backwards-compatible manner.
        major: version when you make incompatible API changes.
    """
    changes = set()
    # Check for renamed modules
    changes.update(compare_names("", api_old, api_new))

    # Check for changes within modules
    for name, new_mod in api_new.items():
        old_mod = api_old.get(name)
        if old_mod:
            changes.update(compare_deep(name, old_mod, new_mod))
    return changes


def compare_names(basename, old_names, new_names):
    removed = (name for name in old_names if name not in new_names)
    added = (name for name in new_names if name not in old_names)

    for name in removed:  # Removed
        yield Change(MAJOR, "Removed: {}".format(join(basename, name)))
    for name in added:  # Added
        yield Change(MINOR, "Added: {}".format(join(basename, name)))


def compare_deep(basename, old_item, new_item):
    changes = set()
    # Map by name
    old_map = {item.name: item for item in old_item}
    new_map = {item.name: item for item in new_item}

    # Check for renames
    changes.update(compare_names(basename, old_map, new_map))

    # Check for changes
    for name, new_item in new_map.items():
        old_item = old_map.get(name)
        if not old_item:
            continue
        abs_name = join(basename, name)
        if type(old_item) != type(new_item):
            changes.add(Change(MAJOR, "Type Changed: {}".format(abs_name)))
        elif isinstance(new_item, (Class, Module)):
            changes.update(
                compare_deep(abs_name, old_item.body, new_item.body)
            )
        elif isinstance(new_item, Func):
            changes.update(compare_func(old_item, new_item))
        elif isinstance(new_item, Var):
            if old_item.type != new_item.type:
                changes.add(Change(MAJOR, "Type Changed: {}".format(abs_name)))
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
    return set()


def join(parent, child):
    return "{}.{}".format(parent, child) if parent else child
