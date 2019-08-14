""" Traverse an API heirarchy """

if False:  # type checking
    from typing import *

import re
import sys
import types
import logging
import os.path
import inspect
import traceback
import importlib

try:
    import builtins  # type: ignore
except ImportError:
    import __builtin__ as builtins  # type: ignore

from surface._base import *
from surface._type import get_type, get_type_func
from surface._utils import clean_repr, import_module, get_signature, get_source
from surface._item_live import ErrorItem, ModuleItem, ClassItem, VarItem, NoneItem, FunctionItem, ParameterItem


LOG = logging.getLogger(__name__)

import_reg = re.compile(r"__init__\.(py[cwd]?|so)$")

builtin_types = tuple(b for b in builtins.__dict__.values() if isinstance(b, type))


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
    def __init__(self, exclude_modules=False, all_filter=False, depth=10):
        LOG.debug(
            "APITraversal created with {}".format(
                ", ".join("{}={}".format(*var) for var in locals().items())
            )
        )
        self.exclude_modules = exclude_modules  # Do not follow exposed modules
        self.all_filter = all_filter  # Mimic "import *"
        self.depth = depth  # How far down the rabbit hole do we go?
        self.scope_api_map = {
            NoneItem: lambda n, s, p: Var(n, "None"),
            VarItem: lambda n, s, p: Var(n, s.get_type()),
            ErrorItem: lambda n, s, p: Unknown(n, clean_repr(s.item)),
            ClassItem: lambda n, s, p: Class(n, tuple(self.walk(s, n, set(p)))),
            ModuleItem: lambda n, s, p: Module(n, s.item.__name__, tuple(self.walk(s, n, set(p)))),
            FunctionItem: lambda n, s, p: Func(n, tuple(self.walk(s, n, set(p))), s.get_return_type()),
            ParameterItem: lambda n, s, p: Arg(n, s.get_type(), s.get_kind()),
        }

    def traverse(self, module, name):
        """ Entry point to generating an API representation. """
        visitors = [
            NoneItem,
            ParameterItem,
            FunctionItem,
            ModuleItem,
            ClassItem,
            VarItem,
        ]
        item = ModuleItem.wrap(visitors, module)
        api = Module(name, module.__name__, tuple(self.walk(item, name, set())))
        return api

    def walk(self, parent_item, parent_name, path):
        LOG.debug("Visiting: {}".format(parent_item))
        if len(path) > self.depth:
            LOG.debug("Exceeded depth")
            return

        item_id = id(parent_item.item)
        if item_id in path:
            yield Unknown(
                parent_name, "Circular Reference: {}".format(clean_repr(repr(parent_item.item)))
            )
            return
        path.add(item_id)

        for name, item in parent_item.items():
            item_type = type(item)
            mapping = self.scope_api_map.get(item_type)
            if mapping:

                yield mapping(name, item, path)

    #
    #
    # def traverse(
    #     self, obj, guard=None
    # ):  # type: (Any, Optional[Set[int]]) -> Iterable[Any]
    #     """ Entry point to generating an API representation. """
    #     if guard is None:  # Guard against infinite recursion
    #         guard = set()
    #     if len(guard) > self.depth:
    #         LOG.debug("Exceeded Depth, {}".format(obj))
    #         return
    #
    #     LOG.debug("Traversing: {}".format(obj))
    #
    #     # NOTE: inspect.getmembers is more comprehensive than dir
    #     # NOTE: but it doesn't allow catching errors on each attribute
    #     # NOTE: getattr_static is also another nice option, python3 only.
    #     attributes = [attr for attr in dir(obj) if self._is_public(attr)]
    #
    #     if self.all_filter:
    #         # __all__ attribute restricts import with *,
    #         # and displays what is intended to be public
    #         whitelist = getattr(obj, "__all__", [])
    #         if whitelist:
    #             attributes = [attr for attr in attributes if attr in whitelist]
    #
    #     # Sort the attributes by name for readability, and diff-ability (is that a word?)
    #     attributes.sort()
    #
    #     # Walk the surface of the object, and extract the information
    #     # In storing a path, make a distinction between modules and their contents
    #     # as a submodule can have the same name as a class in the parent module.
    #     for name in attributes:
    #         # Not sure why this is possible... but it has happened...
    #         if not name:
    #             continue
    #
    #         # NOTE: Consider also supporting python 3 getattr_static for more passive inspection
    #         try:
    #             value = getattr(obj, name)
    #         except Exception as err:
    #             # If we cannot get the attribute, keep going. Just record that the attribute was there.
    #             LOG.debug(traceback.format_exc())
    #             yield Unknown(name, clean_repr(err))
    #             continue
    #
    #         value_id = id(value)
    #         if value_id in guard:
    #             yield Unknown(
    #                 name, "Circular Reference: {}".format(clean_repr(repr(value)))
    #             )
    #         elif value is None:
    #             yield Var(name, "None")
    #         elif value in builtin_types:
    #             yield Var(name, value.__name__)
    #         # Recursable objects
    #         elif inspect.ismodule(value):
    #             if self.exclude_modules:
    #                 continue
    #             if name in sys.builtin_module_names:
    #                 yield Module(name, value.__name__, tuple())
    #             else:
    #                 guard.add(value_id)
    #                 yield self._handle_module(name, value, obj, guard.copy())
    #         elif inspect.isclass(value):
    #             guard.add(value_id)
    #             yield self._handle_class(name, value, obj, guard.copy())
    #         # Python2
    #         elif inspect.ismethod(value):
    #             yield self._handle_method(name, value, obj)
    #         elif inspect.isfunction(value):
    #             # python3
    #             if inspect.isclass(obj):
    #                 yield self._handle_method(name, value, obj)
    #             else:
    #                 yield self._handle_function(name, value, obj)
    #         elif isinstance(value, types.GetSetDescriptorType):
    #             # TODO: Any way to get the result type of value.__get__?
    #             yield Var(name, UNKNOWN)
    #         elif name != "__init__":
    #             yield self._handle_variable(name, value, obj)

    def _handle_function(
        self, name, value, parent
    ):  # type: (str, Any, Any) -> Union[Func, Unknown]
        try:
            sig = get_signature(value)
        except ValueError as err:
            return Unknown(name, clean_repr(err))

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
            sig = get_signature(value)
        except ValueError as err:
            return Unknown(name, clean_repr(err))

        # We want to ignore "self" and "cls", as those are implementation details
        # and are not relevant for API comparisons
        # It seems funcsigs removes "cls" for us in class methods...
        params = list(sig.parameters.items())
        param_types, return_type = get_type_func(value, name, parent)
        source = get_source(value)
        if source and not "@staticmethod" in source and not "@classmethod" in source:
            if len(param_types) == len(params):
                param_types = param_types[1:]
            params = params[1:]
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
