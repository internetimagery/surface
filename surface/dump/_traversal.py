""" Traverse some code. Build a representation from it """
import collections

from pyhike import Chart

from surface.dump._representation import BaseWrapper, Module, Class, Function, Method, ClassMethod, StaticMethod, Attribute


class RepresentationBuilder(Chart):
    """
    Walk through provided objects. Build a mapping of the live objects to our representation.
    """

    _ALLOWED_NAMES = ("__init__", "__new__")

    def __init__(self):
        self._nameMap = {} # type: Dict[str, BaseWrapper]
        self._idMap = {} # type: Dict[int, BaseWrapper]
    
    def get_representation(self):
        # type: () -> Dict[str, Dict[str, BaseWrapper]]
        """ Return our lovely generated representation """
        structure = collections.defaultdict(dict)
        for name, node in self._nameMap.items():
            path, qualname = name.split(":", 1)
            structure[path][qualname] = node
        return structure
    
    def visit_directory(self, name, path, _):
        # type: (str, str, TrailBlazer) -> Optioanl[bool]
        if not self._filter_name(name):
            return True # Prevent looking further into this module

    def visit_file(self, name, path, __):
        # type: (str, str, TrailBlazer) -> Optional[bool]
        if not self._filter_name(name):
            return True # Prevent looking further into this module

    def visit_module(self, name, module, __):
        # type: (str, types.ModuleType, TrailBlazer) -> Optional[bool]
        if not self._filter_name(name):
            return True
        if ":" in name:
            module_wrap = self._get_wrapped(module, Module)
            self._nameMap[name] = module_wrap

    def visit_class(self, name, class_, __):
        # type: (str, type, TrailBlazer) -> Optional[bool]
        if not self._filter_name(name):
            return True
        class_wrap = self._get_wrapped(class_, Class)
        self._nameMap[name] = class_wrap
        return True

    def visit_function(self, name, func, _, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return
        func_wrap = self._get_wrapped(func, Function)
        self._nameMap[name] = func_wrap

    def visit_method(self, name, func, _, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return
        func_wrap = self._get_wrapped(func, Method)
        self._nameMap[name] = func_wrap

    def visit_classmethod(self, name, func, _, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return 
        func_wrap = self._get_wrapped(func, ClassMethod)
        self._nameMap[name] = func_wrap

    def visit_staticmethod(self, name, func, _, __):
        # type: (str, Callable, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return 
        func_wrap = self._get_wrapped(func, StaticMethod)
        self._nameMap[name] = func_wrap

    def visit_attribute(self, name, value, _, __):
        # type: (str, Any, type, TrailBlazer) -> None
        if not self._filter_name(name):
            return 
        attr_wrap = self._get_wrapped(value, Attribute)
        self._nameMap[name] = attr_wrap

    def _filter_name(self, name):
        # type: (str) -> bool
        """ Disallow looking into private variables / classes / modules """
        basename = name.rsplit(".")[-1]
        if basename in self._ALLOWED_NAMES or not basename.startswith("_"):
            return True
        return False
    
    def _get_wrapped(self, object_, wrapper):
        # type: (type, BaseWrapper) -> BaseWrapper
        """ We can keep one representation per live object """
        id_ = id(object_)
        wrapped = self._idMap.get(id_)
        if not wrapped:
            wrapped = self._idMap[id_] = wrapper(object_)
        return wrapped
        