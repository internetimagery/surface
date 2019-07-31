""" Traverse an API heirarchy """

if False:  # type checking
    from typing import *

import re
import logging
import os.path
import inspect
import traceback
import sigtools  # type: ignore
from surface._base import *
from surface._type import get_type, get_type_func
from importlib import import_module


__all__ = ["recurse", "APITraversal"]

LOG = logging.getLogger(__name__)

import_reg = re.compile(r"__init__\.(py[cd]?|so)$")


def recurse(name):  # type: (str) -> List[str]
    """ Given a module path, return paths to its children. """

    stack = [name]
    paths = []

    while stack:
        import_name = stack.pop()
        module = import_module(import_name)
        paths.append(import_name)
        try:
            module_path = module.__file__
        except AttributeError:
            continue

        if not import_reg.search(module_path):
            paths.append(import_name)
            continue

        package = os.path.dirname(module_path)
        submodules = os.listdir(package)
        for submodule in submodules:
            if submodule.startswith("_"):
                pass
            elif submodule.endswith(".py"):
                paths.append("{}.{}".format(import_name, submodule[:-3]))
            elif os.path.isfile(os.path.join(package, submodule, "__init__.py")):
                stack.append("{}.{}".format(import_name, submodule))
    return paths


class APITraversal(object):
    def __init__(self, exclude_modules=False, all_filter=True):
        self.exclude_modules = exclude_modules  # Do not follow exposed modules
        self.all_filter = (
            all_filter
        )  # Filter exposed in the presence of __all__ (like * import)

    def traverse(
        self, obj, guard=None
    ):  # type: (Any, Optional[Set[int]]) -> Iterable[Any]
        """ Entry point to generating an API representation. """
        if guard is None:  # Guard against infinite recursion
            guard = set()

        # NOTE: inspect.getmembers is more comprehensive than dir
        # NOTE: but it doesn't allow catching errors on each attribute
        # NOTE: getattr_static is also another nice option, python3 only.
        attributes = [attr for attr in dir(obj) if self._is_public(attr)]

        if self.all_filter:
            # __all__ attribute restricts import with *,
            # and displays what is intended to be public
            whitelist = getattr(obj, "__all__", [])
            if whitelist:
                attributes = [attr for attr in attributes if attr in whitelist]

        # Sort the attributes by name for readability, and diff-ability (is that a word?)
        attributes.sort()

        # Walk the surface of the object, and extract the information
        # In storing a path, make a distinction between modules and their contents
        # as a submodule can have the same name as a class in the parent module.
        for name in attributes:
            # Not sure why this is possible... but it has happened...
            if not name:
                continue

            # NOTE: Consider also supporting python 3 getattr_static for more passive inspection
            try:
                value = getattr(obj, name)
            except Exception as err:
                # If we cannot get the attribute, keep going. Just record that the attribute was there.
                LOG.debug(traceback.format_exc())
                yield Unknown(name, str(err))
                continue

            value_id = id(value)
            if value_id in guard:
                yield Unknown(name, "Infinite Recursion: {}".format(repr(value)))
                continue

            # Recursable objects
            if inspect.ismodule(value):
                if self.exclude_modules:
                    continue
                guard.add(value_id)
                yield self._handle_module(name, value, obj, guard.copy())
            elif inspect.isclass(value):
                guard.add(value_id)
                yield self._handle_class(name, value, obj, guard.copy())
            # Python2
            elif inspect.ismethod(value):
                yield self._handle_method(name, value, obj)
            elif inspect.isfunction(value):
                # python3
                if inspect.isclass(obj):
                    yield self._handle_method(name, value, obj)
                else:
                    yield self._handle_function(name, value, obj)
            elif name != "__init__":
                yield self._handle_variable(name, value, obj)

    def _handle_function(
        self, name, value, parent
    ):  # type: (str, Any, Any) -> Union[Func, Unknown]
        # TODO: Ensure we find the original classes and methods, and not wrappers.
        # TODO: Though sigtools helps with this somewhat.
        try:
            sig = sigtools.signature(value)
        except SyntaxError as err:
            LOG.debug(traceback.format_exc())
            return Unknown(name, str(err))

        param_types, return_type = get_type_func(value, name, parent)
        return Func(
            name,
            tuple(
                Arg(
                    n,
                    t,
                    self._convert_arg_kind(str(p.kind))
                    | (0 if p.default is sig.empty else DEFAULT),
                )
                for (n, p), t in zip(sig.parameters.items(), param_types)
            ),
            return_type,
        )

    def _handle_method(
        self, name, value, parent
    ):  # type: (str, Any, Any) -> Union[Func, Unknown]
        try:
            sig = sigtools.signature(value)
        except SyntaxError as err:
            LOG.debug(traceback.format_exc())
            return Unknown(name, str(err))

        # We want to ignore "self" and "cls", as those are implementation details
        # and are not relevant for API comparisons
        # It seems sigtools removes "cls" for us in class methods...
        params = list(sig.parameters.items())
        param_types, return_type = get_type_func(value, name, parent)
        try:
            source = inspect.getsource(value)
        except IOError:
            pass
        else:
            if not "@staticmethod" in source and not "@classmethod" in source:
                params = params[1:]
                param_types = param_types[1:]
        return Func(
            name,
            tuple(
                Arg(
                    n,
                    t,
                    self._convert_arg_kind(str(p.kind))
                    | (0 if p.default is sig.empty else DEFAULT),
                )
                for (n, p), t in zip(params, param_types)
            ),
            return_type,
        )

    def _handle_class(
        self, name, value, _, guard
    ):  # type: (str, Any, Any, Set[Any]) -> Class
        return Class(name, tuple(self.traverse(value, guard=guard)))

    @staticmethod
    def _handle_variable(name, value, parent):  # type: (str, Any, Any) -> Var
        return Var(name, get_type(value, name, parent))

    def _handle_module(
        self, name, value, _, guard
    ):  # type: (str, Any, Any, Set[Any]) -> Module
        return Module(name, value.__name__, tuple(self.traverse(value, guard=guard)))

    @staticmethod
    def _is_public(name):  # type: (str) -> bool
        return name == "__init__" or not name.startswith("_")

    @staticmethod
    def _convert_arg_kind(kind):  # type: (str) -> int
        if kind == "POSITIONAL_ONLY":
            return POSITIONAL
        if kind == "KEYWORD_ONLY":
            return KEYWORD
        if kind == "POSITIONAL_OR_KEYWORD":
            return POSITIONAL | KEYWORD
        if kind == "VAR_POSITIONAL":
            return POSITIONAL | VARIADIC
        if kind == "VAR_KEYWORD":
            return KEYWORD | VARIADIC
        raise TypeError("Unknown type.")
