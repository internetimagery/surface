""" Compare two API's """

# TODO: If type changes, check if there was an existing exposed type that matches (eg class "path")
# TODO: If an exposed type is found, declare the type unchanged. As changes in the public api will
# TODO: be picked up by the exposed type entering / leaving the api.

# Python 3.6.0 (v3.6.0:41df79263a11, Dec 23 2016, 08:06:12) [MSC v.1900 64 bit (AMD64)] on win32
# Type "help", "copyright", "credits" or "license" for more information.
# >>> t = "typing.Dict[str, typing.List[_a.MyType]]"
# >>> t
# 'typing.Dict[str, typing.List[_a.MyType]]'
# >>> import re
# >>> re.findall(r"[\w\.~]+", t)
# ['typing.Dict', 'str', 'typing.List', '_a.MyType']
# >>> exit()

# Loop through type identifiers.
# If there is a missmatch...
# maybe unknown check needs to be separate...

# typing.List[~unknown] -> typing.List[typing.List[str]] # different number of identifiers
# ok maybe ast is the best way to go...

# need to make an AstItem class, that takes a source string in a parse argument.
# it needs to do the whole mapping thing, mapping tokens to line/col
# this needs to be wrapped in a namedtuple, and passed through the instances
# then similar to the above, can check if types match by looping through them. But
# will know for sure that we're breaking at the right points, so the unknown example above works.
# as we can just pass over the unknown


if False:  # type checking
    from typing import *


import re

from surface._base import *
from surface._item_static import (
    ModuleAst,
    SubscriptAst,
    NameAst,
    TupleAst,
    UnknownAst,
    AttributeAst,
    SliceAst,
    EllipsisAst,
)

if PY2:
    from itertools import izip_longest as zip_longest, izip as zip  # type: ignore
else:
    from itertools import zip_longest  # type: ignore


RULES = """
API Semantic rules, and how they affect versions.

MAJOR:
  * Removing anything.
  * Renaming keyword-arguments.
  * Adding positional-arguments.
  * Changing types (except where input types become generics).

MINOR:
  * Adding new variables, functions, classes, modules, optional-keyword-arguments, *args, **kwargs.
  * Changing positional-only-argument to positional+keyword.
  * Provide a default to a positional argument.
  * Changing input types to be generics, eg: List to Sequence, Dict to Mapping etc.
  * Unable to verify the change (ie attribute access failed / recursive object).

PATCH:
  * Renaming positional-only-arguments.
  * Adding new typing information (ie was ~unknown, now concrete type).
  * Unknown type remains Unknown.
  * Changing nothing.
"""


# Semantic types
PATCH = "patch"
MINOR = "minor"
MAJOR = "major"

# Templates
_was = '{}, Was: "{}", Now: "{}"'.format
_arg = "{}.({})".format

typing_reg = re.compile(r"typing\.(\w+)")

# Subtype mapping
subtype_map = {
    "Sequence": ("List", "Tuple", "MutableSequence"),
    "Mapping": ("Dict", "MutableMapping"),
    "Set": ("MutableSet",),
    "FrozenSet": ("Set", "MutableSet"),
    "Sized": (
        "Dict",
        "List",
        "Set",
        "Sequence",
        "Mapping",
        "MutableSequence",
        "MutableMapping",
        "MutableSet",
        "FrozenSet",
    ),
}  # type: Dict[str, Tuple[str, ...]]

type_visitors = (
    ModuleAst,
    SubscriptAst,
    NameAst,
    TupleAst,
    UnknownAst,
    AttributeAst,
    SliceAst,
    EllipsisAst,
)


class Comparison(object):
    """
        Compare two API's, and return resulting changes.

        patch: version when you make backwards-compatible bug fixes.
        minor: version when you add functionality in a backwards-compatible manner.
        major: version when you make incompatible API changes.
    """

    def compare_types(self, old_type, new_type):
        print(old_type, new_type)
        # if old_type == new_type:
        #     return None

        # TODO: Check for syntax errors, and then have a fallback
        old_ast = ModuleAst.parse(type_visitors, old_type)
        new_ast = ModuleAst.parse(type_visitors, new_type)

        changes = self._deep_compare_type(old_ast, new_ast)


    def _deep_compare_type(self, old_ast, new_ast, changes=None):
        if changes is None:
            changes = []

        if type(old_ast) != type(new_ast):
            print("TYPE CHANGE", old_ast, new_ast)
        for old_child, new_child in zip(old_ast.values(), new_ast.values()):
            self._deep_compare_type(old_child, new_child, changes)


def compare(
    api_old,  # type: Sequence[Module]
    api_new,  # type: Sequence[Module]
):  # type: (...) -> Set[Change]
    """
        Compare two API's, and return resulting changes.

        patch: version when you make backwards-compatible bug fixes.
        minor: version when you add functionality in a backwards-compatible manner.
        major: version when you make incompatible API changes.
    """
    changes = set()  # type: Set[Change]
    api_old_map = {m.path: m.body for m in api_old}
    api_new_map = {m.path: m.body for m in api_new}

    # Check for renamed modules
    changes.update(compare_names("", api_old_map, api_new_map))

    # Check for changes within modules
    for name, new_mod in api_new_map.items():
        old_mod = api_old_map.get(name)
        if old_mod is not None:
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


# def compare_types(old_type, new_type):



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

            Comparison().compare_types(old_item.type, new_item.type)

            if old_item.type != new_item.type:
                if is_uncovered(old_item.type, new_item.type):
                    changes.add(Change(PATCH, "Uncovered Type", abs_name))
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

    Comparison().compare_types(old_func.returns, new_func.returns)


    if old_func.returns != new_func.returns:
        level = PATCH if is_uncovered(old_func.returns, new_func.returns) else MAJOR
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

        if old_arg and new_arg:
            Comparison().compare_types(old_arg.type, new_arg.type)


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
            level = PATCH if is_uncovered(old_arg.type, new_arg.type) else MAJOR
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


ESC_UNKNOWN = re.escape(UNKNOWN)  # For search replace


def is_uncovered(old_type, new_type):  # type: (str, str) -> bool
    if old_type == UNKNOWN:
        return True
    reg = re.escape(old_type).replace(ESC_UNKNOWN, TYPE_CHARS)
    if re.match(reg, new_type):
        return True
    return False


def is_subtype(subtype, supertype):  # type: (str, str) -> bool
    # If they are the same, nothing to do
    if subtype == supertype:
        return False

    # First check structure
    if typing_reg.sub("~", subtype) != typing_reg.sub("~", supertype):
        return False

    # Structure is the same, compare matching types.
    # It's all or nothing. If one type is a subtype, but others aren't
    # it still needs to be considered false.
    for subt, supert in zip(
        typing_reg.finditer(subtype), typing_reg.finditer(supertype)
    ):
        if subt.group(1) == supert.group(1):
            continue
        subtypes = subtype_map.get(supert.group(1))
        if subtypes is None:
            return False
        if subt.group(1) not in subtypes:
            return False
    return True
