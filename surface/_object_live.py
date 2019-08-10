""" Wrapping live objects """

import inspect
import logging
import traceback
import sigtools

from surface._base import POSITIONAL, KEYWORD, VARIADIC, DEFAULT
from surface._object import Object, ErrorObject
from surface._utils import get_signature
from surface._type import get_type_func

try: # python 3
    from inspect import Parameter, _empty # type: ignore
except ImportError:
    from funcsigs import Parameter, _empty # type: ignore

LOG = logging.getLogger(__name__)


class LiveModule(Object):
    """ Wrap live module objects """

    __slots__ = []

    @staticmethod
    def is_this_type(obj, name, parent):
        return inspect.ismodule(obj)

    def get_child(self, attr):
        try:
            return getattr(self.obj, attr)
        except AttributeError as err:
            LOG.debug(traceback.format_exc())
            raise KeyError(str(err))

    def get_children_names(self):
        return sorted(dir(self.obj))


class LiveClass(LiveModule):
    """ Wrap live class objects """

    __slots__ = []

    NAME_FILTER = staticmethod(lambda n: n == "__init__" or not n.startswith("_"))

    @staticmethod
    def is_this_type(obj, name, parent):
        return inspect.isclass(obj)

    def get_children_names(self):
        names = super(LiveClass, self).get_children_names()
        if not LiveFunction.is_this_type(self.obj.__init__, "__init__", self):
            names = (n for n in names if n != "__init__") # strip init
        return names


class LiveFunction(Object):
    """ Wrap function / method """

    __slots__ = []

    @staticmethod
    def is_this_type(obj, name, parent):
        return inspect.isfunction(obj) or inspect.ismethod(obj)

    def get_child(self, attr):
        sig = get_signature(self.obj)
        return sig.parameters[attr]

    def get_children_names(self):
        sig = get_signature(self.obj)
        return sig.parameters.keys()


class LiveParameter(Object):
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
    def is_this_type(obj, name, parent):
        return isinstance(obj, Parameter)

    def get_type(self):
        return "~unknown"

    def get_kind(self):
        kind = self.KIND_MAP[str(self.obj.kind)] | (0 if self.obj.default is _empty else DEFAULT)
        return kind
