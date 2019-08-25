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

SemVer.MAJOR:
  * Removing anything.
  * Renaming keyword-arguments.
  * Adding positional-arguments.
  * Changing types (except where input types become generics).

SemVer.MINOR:
  * Adding new variables, functions, classes, modules, optional-keyword-arguments, *args, **kwargs.
  * Changing positional-only-argument to positional+keyword.
  * Provide a default to a positional argument.
  * Changing input types to be generics, eg: List to Sequence, Dict to Mapping etc.
  * Unable to verify the change (ie attribute access failed / recursive object).

SemVer.PATCH:
  * Renaming positional-only-arguments.
  * Adding new typing information (ie was ~unknown, now concrete type).
  * API.Unknown type remains API.Unknown.
  * Changing nothing.
"""


# Semantic types
class SemVer(object):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"

# Templates
_was = '{}, Was: "{}", Now: "{}"'.format
_arg = "{}({})".format

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


class Changes(object):
    def compare(
        self, old_api, new_api
    ):  # type: (Sequence[API.Module], Sequence[API.Module]) -> Set[Change]
        """ Run checks over old and new API representations. """

        stack = [
            ("", {mod.name: mod for mod in old_api}, {mod.name: mod for mod in new_api})
        ]
        checks = self._prep_checks()
        changes = set()  # type: Set[Change]

        while stack:
            path, old, new = stack.pop()
            children = set(old) | set(new)
            for child in children:
                old_child = old.get(child)
                new_child = new.get(child)
                if old_child == new_child:
                    continue
                new_path = "{}.{}".format(path, child) if path else child
                for check in checks:
                    if check.will_check(old_child, new_child):
                        changes.update(check.check(new_path, old_child, new_child))
                if isinstance(old_child, (API.Module, API.Class)) and isinstance(
                    new_child, (API.Module, API.Class)
                ):
                    stack.append(
                        (
                            new_path,
                            {item.name: item for item in old_child.body},
                            {item.name: item for item in new_child.body},
                        )
                    )

        return changes

    def _prep_checks(self):
        return [
            AddRemoveCheck(),
            CannotVerifyCheck(),
            TypeMatchCheck(),
            TypingCheck(),
            ArgKindCheck(),
            ArgAddRemoveCheck(),
            ArgTypeCheck(),
        ]


class Check(object):
    """ Base check object, used for all checks """

    def will_check(self, old, new):  # type: (Any, Any) -> bool
        return False

    def check(self, path, old, new):  # type: (str, Any, Any) -> List[Change]
        return []


class AddRemoveCheck(Check):
    """ Check things have been added / removed. """

    def will_check(self, _, __):
        return True

    def check(self, path, old, new):
        if old is None:
            return [Change(SemVer.MINOR, "Added", path)]
        if new is None:
            return [Change(SemVer.MAJOR, "Removed", path)]
        return []


class CannotVerifyCheck(Check):
    """ Check for unverifyable changes. """

    def will_check(self, old, new):
        if old is None or new is None:
            return False
        return isinstance(old, API.Unknown) or isinstance(new, API.Unknown)

    def check(self, path, old, new):
        info = old.info if isinstance(old, API.Unknown) else new.info
        return [Change(SemVer.MINOR, "Could not verify", "{}: {}".format(path, info))]


class TypeMatchCheck(Check):
    """ Check for type changes with the same name. """

    def will_check(self, old, new):
        if (
            old is None
            or new is None
            or type(old) == type(new)
            or isinstance(old, API.Unknown)
            or isinstance(new, API.Unknown)
        ):
            return False
        return True

    def check(self, path, old, new):
        return [Change(SemVer.MAJOR, "Type Changed", _was(path, type(old), type(new)))]


class TypingCheck(Check):
    def will_check(self, old, new):
        return isinstance(old, API.Var) and isinstance(new, API.Var)

    def check(self, path, old, new):
        if old.type == new.type:
            return []
        if is_uncovered(old.type, new.type):
            level = SemVer.PATCH
        elif is_subtype(old.type, new.type):
            level = SemVer.MINOR
        else:
            level = SemVer.MAJOR
        return [Change(level, "Type Changed", _was(path, old.type, new.type))]


class ArgKindCheck(Check):
    """ Check if function arguments changed their type """

    def will_check(self, old, new):
        return isinstance(old, API.Func) and isinstance(new, API.Func)

    def check(self, path, old, new):
        old_names = {arg.name: arg for arg in old.args}
        new_names = {arg.name: arg for arg in new.args}
        changes = []
        for name, new_arg in new_names.items():
            old_arg = old_names.get(name)
            if old_arg is None or old_arg.kind == new_arg.kind:
                continue
            if new_arg.kind == old_arg.kind | Kind.KEYWORD:
                level = SemVer.MINOR  # Adding keyword is not breaking.
            elif new_arg.kind == old_arg.kind | Kind.DEFAULT:
                level = SemVer.MINOR  # Adding default is not breaking.
            else:
                level = SemVer.MAJOR
            changes.append(Change(level, "Kind Changed", _arg(path, name)))
        return changes


class ArgAddRemoveCheck(ArgKindCheck):
    """ Check if functions arguments are added / removed. """

    def check(self, path, old, new):
        changes = []
        for old_arg, new_arg in self.positionals(old.args, new.args):
            if old_arg == new_arg:
                continue
            elif not old_arg:
                # Adding a new optional arg (ie: arg=None) or variadic (ie *args / **kwargs)
                # is not a breaking change. Adding anything else is.
                level = (
                    SemVer.MINOR if new_arg.kind & (Kind.VARIADIC | Kind.DEFAULT) else SemVer.MAJOR
                )
                changes.append(Change(level, "Added API.Arg", _arg(path, new_arg.name)))
            elif not new_arg:
                # Removing an argument is always a breaking change.
                changes.append(
                    Change(SemVer.MAJOR, "Removed API.Arg", _arg(path, old_arg.name))
                )
            elif old_arg.name != new_arg.name:
                # It's not breaking to rename variadic or positional-only args, but is for anything else
                level = (
                    SemVer.PATCH
                    if new_arg.kind == old_arg.kind
                    and (
                        new_arg.kind & Kind.VARIADIC or new_arg.kind == Kind.POSITIONAL
                    )
                    else SemVer.MAJOR
                )
                changes.append(
                    Change(
                        level,
                        "Renamed API.Arg",
                        _was(_arg(path, new_arg.name), old_arg.name, new_arg.name),
                    )
                )

        old_kwargs, new_kwargs = self.keywords(old.args, new.args)
        for name in set(old_kwargs) | set(new_kwargs):
            old_kwarg = old_kwargs.get(name)
            new_kwarg = new_kwargs.get(name)
            if old_kwarg == new_kwarg:
                continue
            elif old_kwarg is None:
                return [Change(SemVer.MINOR, "Added API.Arg", _arg(path, name))]
            elif new_kwarg is None:
                return [Change(SemVer.MAJOR, "Removed API.Arg", _arg(path, name))]
        return changes

    @staticmethod
    def positionals(old, new):
        return zip_longest(
            (
                arg
                for arg in old
                if arg.kind & Kind.POSITIONAL
                or arg.kind == (Kind.KEYWORD | Kind.VARIADIC)
            ),
            (
                arg
                for arg in new
                if arg.kind & Kind.POSITIONAL
                or arg.kind == (Kind.KEYWORD | Kind.VARIADIC)
            ),
        )

    @staticmethod
    def keywords(old, new):
        return (
            {
                arg.name: arg
                for arg in old
                if not arg.kind & (Kind.POSITIONAL | Kind.VARIADIC)
            },
            {
                arg.name: arg
                for arg in new
                if not arg.kind & (Kind.POSITIONAL | Kind.VARIADIC)
            },
        )


class ArgTypeCheck(ArgAddRemoveCheck):
    @classmethod
    def check(self, path, old, new):
        changes = []

        for old_arg, new_arg in self.positionals(old.args, new.args):
            if old_arg is None or new_arg is None:
                continue
            if old_arg.type != new_arg.type:
                if is_uncovered(old_arg.type, new_arg.type):
                    level = SemVer.PATCH
                elif is_subtype(old_arg.type, new_arg.type):
                    level = SemVer.MINOR
                else:
                    level = SemVer.MAJOR
                changes.append(
                    Change(
                        level,
                        "Type Changed",
                        _was(_arg(path, new_arg.name), old_arg.type, new_arg.type),
                    )
                )

        old_kwargs, new_kwargs = self.keywords(old.args, new.args)
        for name, new_kwarg in new_kwargs.items():
            old_kwarg = old_kwargs.get(name)
            if old_kwarg is None:
                continue
            if old_kwarg.type != new_kwarg.type:
                if is_uncovered(old_kwarg.type, new_kwarg.type):
                    level = SemVer.PATCH
                elif is_subtype(old_kwarg.type, new_kwarg.type):
                    level = SemVer.MINOR
                else:
                    level = SemVer.MAJOR
                changes.append(
                    Change(
                        level,
                        "Type Changed",
                        _was(
                            _arg(path, new_kwarg.name), old_kwarg.type, new_kwarg.type
                        ),
                    )
                )

        if old.returns != new.returns:
            if is_uncovered(old.returns, new.returns):
                level = SemVer.PATCH
            else:
                level = SemVer.MAJOR
            changes.append(
                Change(
                    level, "Return Type Changed", _was(path, old.returns, new.returns)
                )
            )

        return changes


class TypingChanges(object):

    _type_visitors = (
        ModuleAst,
        SubscriptAst,
        NameAst,
        TupleAst,
        UnknownAst,
        AttributeAst,
        SliceAst,
        EllipsisAst,
    )

    def compare(self, old, new):
        pass

    def _prep_checks(self):
        return []


class UncoveredTypingCheck(Check):
    def will_check(self, old, new):
        return isinstance(old, UnknownAst) or isinstance(new, UnknownAst)

    def check(self, path, old, new):
        if isinstance(old, UnknownAst):
            if isinstance(new, UnknownAst):
                return []
            return [Change(SemVer.PATCH, "Uncovered Type", _was(path, old, new))]
        return [Change(SemVer.MINOR, "Lost Type", _was(path, old, new))]


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
