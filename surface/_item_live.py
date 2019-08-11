""" Wrapping live objects """

import sys
import inspect
import logging
import traceback
import sigtools

from surface._base import POSITIONAL, KEYWORD, VARIADIC, DEFAULT, UNKNOWN
from surface._utils import get_signature
from surface._type import get_type_func, format_annotation

from surface._item import Item

try: # python 3
    from inspect import Parameter, _empty as Empty # type: ignore
except ImportError:
    from funcsigs import Parameter, _empty as Empty # type: ignore

LOG = logging.getLogger(__name__)


class ErrorItem(Item):
    """ Special Item to represent errors attained from unreachable items. """

    __slots__ = ("type", "trace")

    def __new__(cls, parent=None): # type: (Optional[Item]) -> ErrorItem
        errType, errVal, errTrace = sys.exc_info()
        scope = super(ErrorItem, cls).__new__(cls, [], errVal, parent)
        scope.type = errType
        scope.trace = traceback.format_exc()
        LOG.debug(scope.trace) # Alert us of this error
        return scope


class LiveItem(Item):
    """ Wrap and traverse live objects """

    __slots__ = []

    def __getitem__(self, name): # type: (str) -> Item
        """ We can get errors while traversing. Keep them. """
        try:
            return super(LiveItem, self).__getitem__(name)
        except Exception:
            return ErrorItem(self)


class ModuleItem(LiveItem):
    """ Wrap live module objects """

    __slots__ = []

    ALL_FILTER = False
    EXCLUDE_MODULES = False

    @classmethod
    def is_this_type(cls, item, parent):
        if cls.EXCLUDE_MODULES and parent:
            return False
        return inspect.ismodule(item)

    def get_child(self, attr):
        return getattr(self.item, attr)

    def get_children_names(self):
        names = (name for name in sorted(dir(self.item)) if not name.startswith("_"))
        if self.ALL_FILTER:
            try:
                all_filter = self.item.__all__
            except AttributeError:
                pass
            else:
                names = (name for name in names if name in all_filter)
        return names


class ClassItem(LiveItem):
    """ Wrap live class objects """

    __slots__ = []

    @staticmethod
    def is_this_type(item, parent):
        return inspect.isclass(item)

    def get_children_names(self):
        names = (name for name in sorted(dir(self.item)) if name == "__init__" or not name.startswith("_"))
        if not FunctionItem.is_this_type(self.item.__init__, self):
            names = (n for n in names if n != "__init__") # strip init
        return names

    def get_child(self, attr):
        return getattr(self.item, attr)


class VarItem(LiveItem):
    """ Wrap variable. Fallback. """

    __slots__ = []

    @staticmethod
    def is_this_type(item, parent):
        return True

    def get_type(self):
        return "~unknown"


class FunctionItem(LiveItem):
    """ Wrap function / method """

    __slots__ = []

    @staticmethod
    def is_this_type(obj, parent):
        return inspect.isfunction(obj) or inspect.ismethod(obj)

    def get_child(self, attr):
        sig = get_signature(self.item)
        return sig.parameters[attr]

    def get_children_names(self):
        sig = get_signature(self.item)
        return sig.parameters.keys()

    def get_return_type(self):
        return "~unknown"


class ParameterItem(LiveItem):
    """ Wrap function parameter """

    __slots__ = []

    KIND_MAP = {
        "POSITIONAL_ONLY": POSITIONAL,
        "KEYWORD_ONLY": KEYWORD,
        "POSITIONAL_OR_KEYWORD": POSITIONAL | KEYWORD,
        "VAR_POSITIONAL": POSITIONAL | VARIADIC,
        "VAR_KEYWORD": KEYWORD | VARIADIC,
    }

    @staticmethod
    def is_this_type(item, parent):
        return isinstance(item, Parameter)

    def get_type(self):
        if self.item.annotation != Empty:
            return format_annotation(self.item.annotation)
        return UNKNOWN

    def get_kind(self):
        kind = self.KIND_MAP[str(self.item.kind)] | (0 if self.item.default is Empty else DEFAULT)
        return kind




# class ModuleMap(object):
#     """ Map Objects to modules """
#
#     _cache = {} # type: Dict[Any, Dict[int, Any]]
#
#     @classmethod
#     def get_wrapper(cls, obj):
#         module = inspect.getmodule(obj)
#         if not module:
#             return None
#         if module not in cls._cache:
#             print("not here", module)
#             cls._cache[module] = {}
#             wrap_mod = Object.wrap(module, module.__name__)
#             cls.add(wrap_mod, module)
#             cls.walk(wrap_mod, module)
#         return cls._cache.get(module, {}).get(id)
#
#     @classmethod
#     def add(cls, wrapper, home):
#         module = inspect.getmodule(wrapper.obj)
#         if not module or module != home:
#             return
#         obj_id = id(wrapper.obj)
#         if obj_id in cls._cache[module]:
#             return
#         cls._cache[module][id(wrapper.obj)] = wrapper
#
#     @classmethod
#     def walk(cls, wrapper, home):
#         # Walk shallow first
#         children = list(wrapper.values())
#         for wrap in children:
#             cls.add(wrap, home)
#         for wrap in children:
#             cls.walk(wrap, home)
#
# # TODO: wrap things. get children different way?
