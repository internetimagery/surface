""" Compare two API's """

# TODO: Better formatted output diff
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

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
            changes.update(compare_deep(abs_name, old_item.body, new_item.body))
        elif isinstance(new_item, Func):
            changes.update(compare_func(abs_name, old_item, new_item))
        elif isinstance(new_item, Var):
            if old_item.type != new_item.type:
                changes.add(Change(MAJOR, "Type Changed: {}".format(abs_name)))
        else:
            raise TypeError("Unknown type {}".format(type(new_item)))

    return changes


def compare_func(basename, old_func, new_func):
    changes = set()

    if old_func.returns != new_func.returns:
        changes.add(Change(MAJOR, "Return Type Changed: {}".format(basename)))

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
            changes.add(
                Change(level, "Added Arg: {}.({})".format(basename, new_arg.name))
            )
            continue
        elif not new_arg:
            # Removing an argument is always a breaking change.
            changes.add(
                Change(MAJOR, "Removed Arg: {}.({})".format(basename, old_arg.name))
            )
            continue

        name = "{}.({})".format(basename, new_arg.name)
        if old_arg.name != new_arg.name:
            # It's not breaking to rename variadic or positional-only args, but is for anything else
            level = (
                PATCH
                if new_arg.kind == old_arg.kind
                and (new_arg.kind & VARIADIC or new_arg.kind == POSITIONAL)
                else MAJOR
            )
            changes.add(Change(level, "Renamed Arg: {}".format(name)))
        if old_arg.type != new_arg.type:
            changes.add(Change(MAJOR, "Type Changed: {}".format(name)))
        if old_arg.kind != new_arg.kind:
            # Adding a default to an argument is not a breaking change.
            level = MINOR if new_arg.kind == (old_arg.kind | DEFAULT) else MAJOR
            changes.add(Change(level, "Kind Changed: {}".format(name)))

    # Check for changes to keyword only arguments
    old_keyword = set(
        "({})".format(arg.name) for arg in old_func.args if arg.kind == KEYWORD
    )
    new_keyword = set(
        "({})".format(arg.name) for arg in new_func.args if arg.kind == KEYWORD
    )
    changes.update(compare_names(basename, old_keyword, new_keyword))

    # Finally, check variadic keyword (eg **kwargs)
    old_var_keyword = [arg for arg in old_func.args if arg.kind & (KEYWORD | VARIADIC)]
    new_var_keyword = [arg for arg in new_func.args if arg.kind & (KEYWORD | VARIADIC)]
    if new_var_keyword == old_var_keyword:
        pass
    elif old_var_keyword and not new_var_keyword:
        changes.add(
            Change(
                MAJOR, "Removed Arg: {}.({})".format(basename, old_var_keyword[0].name)
            )
        )
    elif new_var_keyword and not old_var_keyword:
        changes.add(
            Change(
                MINOR, "Added Arg: {}.({})".format(basename, new_var_keyword[0].name)
            )
        )
    elif new_var_keyword[0].name != old_var_keyword[0].name:
        changes.add(
            Change(
                PATCH, "Renamed Arg: {}.({})".format(basename, new_var_keyword[0].name)
            )
        )

    return changes


def join(parent, child):
    return "{}.{}".format(parent, child) if parent else child
