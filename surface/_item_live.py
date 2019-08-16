""" Wrapping live objects """

if False:  # type checking
    from typing import *

import sys
import inspect
import logging
import traceback
import sigtools  # type: ignore

from surface._base import POSITIONAL, KEYWORD, VARIADIC, DEFAULT, UNKNOWN
from surface._utils import get_signature
from surface._type import get_type, get_type_func, format_annotation

from surface._item import Item

try:  # python 3
    import builtins  # type: ignore
except ImportError:
    import __builtin__ as builtins  # type: ignore

try:  # python 3
    from inspect import Parameter, _empty as Empty  # type: ignore
except ImportError:
    from funcsigs import Parameter, _empty as Empty  # type: ignore

LOG = logging.getLogger(__name__)

BUILTIN_TYPES = tuple(b for b in builtins.__dict__.values() if isinstance(b, type))


class ErrorItem(Item):
    """ Special Item to represent errors attained from unreachable items. """

    __slots__ = ("type", "trace")

    def __new__(cls, parent=None):  # type: (Optional[Any]) -> ErrorItem
        errType, errVal, errTrace = sys.exc_info()
        scope = super(ErrorItem, cls).__new__(cls, [], errVal, parent)  # type: Any
        scope.type = errType
        scope.trace = traceback.format_exc()
        LOG.debug(scope.trace)  # Alert us of this error
        return scope


class LiveItem(Item):
    """ Wrap and traverse live objects """

    __slots__ = []  # type: ignore
    _cache = {}  # type: Dict[int, Any]

    @classmethod
    def wrap(cls, visitors, item, parent=None):
        item_id = id(item)
        if item_id not in cls._cache:
            cls._cache[item_id] = super(LiveItem, cls).wrap(visitors, item, parent)
        return cls._cache[item_id]

    def __getitem__(self, name):  # type: (str) -> Item
        """ We can get errors while traversing. Keep them. """
        try:
            return super(LiveItem, self).__getitem__(name)
        except Exception:
            return ErrorItem(self)

    @property
    def name(self):
        return getattr(self.item, "__name__", "")

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.name)


class ModuleItem(LiveItem):
    """ Wrap live module objects """

    __slots__ = []  # type: ignore

    ALL_FILTER = False
    BLACK_LIST = "pkg_resources"

    @classmethod
    def is_this_type(cls, item, parent):
        return inspect.ismodule(item)

    def get_child(self, attr):
        return getattr(self.item, attr)

    def get_children_names(self):
        if self.name in sys.builtin_module_names:
            return []  # Don't bother traversing built in stuff...
        if self.name in self.BLACK_LIST:  # Ignore specific modules
            return []
        names = (
            name for name in sorted(dir(self.item)) if name and not name.startswith("_")
        )
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

    __slots__ = []  # type: ignore

    @staticmethod
    def is_this_type(item, parent):
        return inspect.isclass(item)

    def get_children_names(self):
        names = [name for name in sorted(dir(self.item)) if not name.startswith("_")]
        if hasattr(self.item, "__init__") and FunctionItem.is_this_type(
            self.item.__init__, self
        ):
            names.append("__init__")
        if hasattr(self.item, "__new__") and FunctionItem.is_this_type(
            self.item.__new__, self
        ):
            names.append("__new__")
        return names

    def get_child(self, attr):
        return getattr(self.item, attr)


class VarItem(LiveItem):
    """ Wrap variable. Fallback. """

    __slots__ = []  # type: ignore

    @staticmethod
    def is_this_type(item, parent):
        return True

    def get_type(self):
        return get_type(self.item)


class BuiltinItem(LiveItem):
    """ Wrap builtin. """

    __slots__ = []  # type: ignore

    @staticmethod
    def is_this_type(item, parent):
        return item in BUILTIN_TYPES

    def get_type(self):
        return self.item.__name__


class NoneItem(LiveItem):
    """ Wrap None. """

    __slots__ = []  # type: ignore

    @staticmethod
    def is_this_type(item, parent):
        return item is None


class FunctionItem(LiveItem):
    """ Wrap function / method """

    __slots__ = []  # type: ignore

    @staticmethod
    def is_this_type(item, parent):
        return inspect.isfunction(item) or inspect.ismethod(item)

    def get_child(self, attr):
        sig = get_signature(self.item)
        return sig.parameters[attr]

    def get_children_names(self):
        sig = get_signature(self.item)
        if not sig:
            return []

        params = list(sig.parameters.keys())

        if isinstance(self.parent, ClassItem):
            # We want to ignore "self" and "cls", as those are implementation details
            # and are not relevant for API comparisons
            # It seems funcsigs removes "cls" for us in class methods... that is nice.
            source_func = sorted(sig.sources["+depths"].items(), key=lambda s: s[1])[
                -1
            ][0]
            if self.is_method:
                params = params[1:]  # chop off self
        return params

    def get_return_type(self):
        func_type = get_type_func(self.item)
        if not func_type:
            return UNKNOWN
        return func_type[1]

    @property
    def is_method(self):
        """ Check if function is a method (also not staticmethod or classmethod) """
        if not isinstance(self.parent, ClassItem):
            return False
        name = self.name
        for parent in inspect.getmro(self.parent.item):
            dct = getattr(parent, "__dict__", {})
            if name not in dct:
                continue
            func = dct[name]
            if isinstance(func, (staticmethod, classmethod)):
                return False
            break
        return True


class ParameterItem(LiveItem):
    """ Wrap function parameter """

    __slots__ = []  # type: ignore

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
            print("I HAVE AN ANNOTATION", self.item)
            return UNKNOWN
        else:
            func_type = get_type_func(self.parent.item)
            if func_type:
                return func_type[0].get(self.item.name, UNKNOWN)
        return UNKNOWN

    def get_kind(self):
        kind = self.KIND_MAP[str(self.item.kind)] | (
            0 if self.item.default is Empty else DEFAULT
        )
        return kind
