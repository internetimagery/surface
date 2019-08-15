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
from surface._item_live import (
    ErrorItem,
    ModuleItem,
    ClassItem,
    VarItem,
    BuiltinItem,
    NoneItem,
    FunctionItem,
    ParameterItem,
)


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


class Traversal(object):
    def __init__(
        self, exclude_modules=False, all_filter=False, depth=6
    ):  # type: (bool, bool, int) -> None
        LOG.debug(
            "Traversal created with {}".format(
                ", ".join("{}={}".format(*var) for var in locals().items())
            )
        )
        self.exclude_modules = exclude_modules  # Do not follow exposed modules
        self.all_filter = all_filter  # Mimic "import *"
        self.depth = depth  # How far down the rabbit hole do we go?
        self.item_map = {
            NoneItem: lambda n, s, p: Var(n, "None"),
            VarItem: lambda n, s, p: Var(n, s.get_type()),
            BuiltinItem: lambda n, s, p: Var(n, s.get_type()),
            ErrorItem: lambda n, s, p: Unknown(n, clean_repr(s.item)),
            ClassItem: lambda n, s, p: Class(n, tuple(self.walk(s, n, p.copy()))),
            ModuleItem: lambda n, s, p: Module(
                n,
                s.item.__name__,
                tuple([] if self.exclude_modules else self.walk(s, n, p.copy())),
            ),
            FunctionItem: lambda n, s, p: Func(
                n, tuple(self.walk(s, n, set(p))), s.get_return_type()
            ),
            ParameterItem: lambda n, s, p: Arg(n, s.get_type(), s.get_kind()),
        }  # type: Dict[Any, Any]

    def traverse(self, module):  # type: (Any) -> Module
        """ Entry point to generating an API representation. """
        visitors = [
            NoneItem,
            BuiltinItem,
            ParameterItem,
            FunctionItem,
            ModuleItem,
            ClassItem,
            VarItem,
        ]
        ModuleItem.ALL_FILTER = self.all_filter
        name = module.__name__.rsplit(".", 1)[-1]
        item = ModuleItem.wrap(visitors, module)
        api = Module(name, module.__name__, tuple(self.walk(item, name, set())))
        return api

    def walk(
        self, current_item, current_name, path
    ):  # type: (Any, str, Set[int]) -> Iterable[Any]
        LOG.debug("Visiting: {}".format(current_item))

        # Recursable types
        if isinstance(current_item, (ModuleItem, ClassItem)):
            if len(path) > self.depth:
                LOG.debug("Exceeded depth")
                return

            item_id = id(current_item.item)
            if item_id in path:
                yield Unknown(
                    current_name,
                    "Circular Reference: {}".format(
                        clean_repr(repr(current_item.item))
                    ),
                )
                return
            path.add(item_id)

        for name, item in current_item.items():
            item_type = type(item)
            api_gen = self.item_map.get(item_type)
            if api_gen:
                yield api_gen(name, item, path)
