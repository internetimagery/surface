""" Traverse an API heirarchy """

if False:  # type checking
    from typing import *

import re
import sys
import types
import logging
import os.path
import importlib

from surface._base import *
from surface._utils import clean_repr, clamp_string
from surface._item_live import (
    ErrorItem,
    ModuleItem,
    ClassItem,
    VarItem,
    EnumItem,
    BuiltinItem,
    NoneItem,
    FunctionItem,
    ParameterItem,
)


LOG = logging.getLogger(__name__)


CircularWarn = "Circular Reference"
DepthWarn = "Depth Exceeded"

import_reg = re.compile(r"__init__\.(py[cwd]?|so)$")


def recurse(name):  # type: (str) -> List[str]
    """ Given a module path, return paths to its children. """

    stack = [name]
    paths = []

    while stack:
        import_name = stack.pop()
        module = importlib.import_module(import_name)
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
            NoneItem: lambda n, s, p: API.Var(n, "NoneType"),
            EnumItem: lambda n, s, p: API.Var(n, s.get_type()),
            VarItem: lambda n, s, p: API.Var(n, s.get_type()),
            BuiltinItem: lambda n, s, p: API.Var(n, s.get_type()),
            ErrorItem: lambda n, s, p: API.Unknown(
                n, s.type, clamp_string(clean_repr(s.item))
            ),
            ClassItem: lambda n, s, p: API.Class(
                n, s.get_type(), tuple(self.walk(s, n, p.copy()))
            ),
            ModuleItem: lambda n, s, p: API.Module(
                n,
                s.get_type(),
                tuple([] if self.exclude_modules else self.walk(s, n, p.copy())),
            ),
            FunctionItem: lambda n, s, p: API.Func(
                n, tuple(self.walk(s, n, set(p))), s.get_return_type()
            ),
            ParameterItem: lambda n, s, p: API.Arg(n, s.get_type(), s.get_kind()),
        }  # type: Dict[Any, Any]

    def traverse(self, module):  # type: (Any) -> API.Module
        """ Entry point to generating an API representation. """
        visitors = [
            NoneItem,
            EnumItem,
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
        api = API.Module(name, module.__name__, tuple(self.walk(item, name, set())))
        return api

    def walk(
        self, current_item, current_name, path
    ):  # type: (Any, str, Set[int]) -> Iterable[Any]
        LOG.debug("Visiting: {}".format(current_item))

        # Recursable types
        depth_exceeded = False
        if isinstance(current_item, (ModuleItem, ClassItem)):
            if len(path) >= self.depth:
                LOG.debug("Exceeded depth")
                depth_exceeded = True

            item_id = id(current_item.item)
            if item_id in path:
                yield API.Unknown(
                    current_name,
                    CircularWarn,
                    clamp_string(clean_repr(repr(current_item.item))),
                )
                return
            path.add(item_id)

        for name, item in current_item.items():
            if depth_exceeded:
                yield API.Unknown(
                    name, DepthWarn, clamp_string(clean_repr(repr(item.item)))
                )
                continue

            item_type = type(item)
            api_gen = self.item_map.get(item_type)
            if api_gen:
                yield api_gen(name, item, path)
