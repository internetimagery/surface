""" Traverse some code. Build a representation from it """
from typing import Dict

import collections

from pyhike import Chart

from surface.dump._representation import (
    name_split,
    BaseWrapper,
    Module,
    Class,
    Function,
    Method,
    ClassMethod,
    StaticMethod,
    Property,
    Attribute,
    BAD_NAME,
)
from surface.dump._plugins import (
    PluginManager,
    AnnotationTypingPlugin,
    CommentTypingPlugin,
    DocstringTypingPlugin,
)

Representation = Dict[str, Dict[str, BaseWrapper]]


class RepresentationBuilder(Chart):
    """
    Walk through provided objects. Build a mapping of the live objects to our representation.
    """

    def __init__(self, path_filter=None, filter_allowed_only=False):
        # type: (Optional[Callable[[str], bool]], bool) -> None
        self._path_filter = path_filter or (lambda p: True)
        self._disallowed_paths = set(("builtins", "__builtin__"))
        self._allowed_names = set(("__init__", "__new__"))
        self._nameMap = {}  # type: Dict[str, BaseWrapper]
        self._idMap = {}  # type: Dict[int, BaseWrapper]
        self._plugin = PluginManager(
            [AnnotationTypingPlugin(), CommentTypingPlugin(), DocstringTypingPlugin()],
        )  # type: List[BasePlugin]
        self._filter_allowed_only = filter_allowed_only

    def get_representation(self):
        # type: () -> Representation
        """ Return our lovely generated representation """
        structure = collections.defaultdict(dict)
        for name, node in self._nameMap.items():
            path, qualname = name.split(":", 1)
            structure[path][qualname] = node
        return structure

    def visit_directory(self, name, path, _):
        # type: (str, str, TrailBlazer) -> Optioanl[bool]
        if not self._filter_name(name):
            return True  # Prevent looking further into this module

    def visit_file(self, name, path, __):
        # type: (str, str, TrailBlazer) -> Optional[bool]
        if not self._filter_name(name):
            return True  # Prevent looking further into this module

    def visit_module(self, name, module, __):
        # type: (str, types.ModuleType, TrailBlazer) -> Optional[bool]
        if not self._filter_name(name):
            return True
        # Only track modules that have been imported
        if ":" in name:
            module_wrap = self._get_wrapped(module)
            if module_wrap:
                self._nameMap[name] = module_wrap
                # We have visited this module. Don't need to do it again.
                return True
            self._nameMap[name] = module_wrap = self._set_wrapped(
                Module(module, None, self._plugin)
            )
            if self._filter_allowed_only and not self._path_filter(
                module_wrap.get_name()
            ):
                # Requested we do not traverse unspecified
                return True

    def visit_class(self, name, class_, __):
        # type: (str, type, TrailBlazer) -> Optional[bool]
        if not self._filter_name(name):
            return True
        class_wrap = self._get_wrapped(class_)
        if class_wrap:
            self._nameMap[name] = class_wrap
            # We have already visited this class. Don't need to do it again.
            return True
        self._nameMap[name] = class_wrap = self._set_wrapped(
            Class(class_, None, self._plugin)
        )
        if self._filter_allowed_only and self._path_filter(class_wrap.get_definition()):
            # Requested we do not traverse unspecified
            return True

    def visit_function(self, name, func, parent, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return
        func_wrap = self._get_wrapped(func) or self._set_wrapped(
            Function(func, parent, self._plugin)
        )
        self._nameMap[name] = func_wrap

    def visit_method(self, name, func, parent, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return
        func_wrap = self._get_wrapped(func) or self._set_wrapped(
            Method(func, parent, self._plugin)
        )
        self._nameMap[name] = func_wrap

    def visit_classmethod(self, name, func, parent, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return
        func_wrap = self._get_wrapped(func) or self._set_wrapped(
            ClassMethod(func, parent, self._plugin)
        )
        self._nameMap[name] = func_wrap

    def visit_staticmethod(self, name, func, parent, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return
        func_wrap = self._get_wrapped(func) or self._set_wrapped(
            StaticMethod(func, parent, self._plugin)
        )
        self._nameMap[name] = func_wrap

    def visit_property(self, name, descriptor, parent, _):
        if not self._filter_name(name):
            return
        desc_wrap = self._get_wrapped(descriptor) or self._set_wrapped(
            Property(descriptor, parent, self._plugin)
        )
        self._nameMap[name] = desc_wrap

    def visit_attribute(self, name, value, parent, __):
        # type: (str, Any, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return
        attr_wrap = self._get_wrapped(value) or self._set_wrapped(
            Attribute(value, parent, self._plugin)
        )
        self._nameMap[name] = attr_wrap

    def _filter_name(self, name):
        # type: (str) -> bool
        """ Disallow looking into private variables / classes / modules """
        # Compare module with whitelist, this can bypass the "only private" rule
        name_parts = name.split(":")
        path_basename = name_split(name_parts[0])[-1]
        if name_parts[0] in self._disallowed_paths:
            path_allowed = False
        elif self._path_filter(name_parts[0]) or not path_basename.startswith("_"):
            path_allowed = True
        else:
            path_allowed = False

        if len(name_parts) == 1:
            # We only have a path, so we can accept names
            name_allowed = True
        else:
            name_basename = name_split(name_parts[1])[-1]
            name_allowed = (
                True
                if not BAD_NAME.match(name_basename)
                and (
                    name_basename in self._allowed_names
                    or not name_basename.startswith("_")
                )
                else False
            )

        return path_allowed and name_allowed

    def _get_wrapped(self, object_):
        # type: (type) -> BaseWrapper
        """ We can keep one representation per live object """
        id_ = id(object_)
        return self._idMap.get(id_)

    def _set_wrapped(self, wrapper):
        # type: (BaseWrapper) -> BaseWrapper
        """ Assign wrapper """
        self._idMap[wrapper.get_id()] = wrapper
        return wrapper
