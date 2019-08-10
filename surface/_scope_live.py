""" Scopes for live objects """

import inspect
import logging
import traceback
import sigtools

from surface._base import POSITIONAL, KEYWORD, VARIADIC, DEFAULT
from surface._scope import Scope, ErrorScope
from surface._utils import get_signature

try: # python 3
    from inspect import Parameter, _empty # type: ignore
except ImportError:
    from funcsigs import Parameter, _empty # type: ignore

LOG = logging.getLogger(__name__)


class LiveModuleScope(Scope):
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


class LiveClassScope(LiveModuleScope):
    """ Wrap live class objects """

    __slots__ = []

    NAME_FILTER = staticmethod(lambda n: n == "__init__" or not n.startswith("_"))

    @staticmethod
    def is_this_type(obj, name, parent):
        return inspect.isclass(obj)

    def get_children_names(self):
        names = super(LiveClassScope, self).get_children_names()
        if not LiveFunctionScope.is_this_type(self.obj.__init__, "__init__", self):
            names = (n for n in names if n != "__init__") # strip init
        return names


class LiveFunctionScope(Scope):
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


class LiveParameterScope(Scope):
    """ Wrap function parameter """

    __slots__ = []

    @staticmethod
    def is_this_type(obj, name, parent):
        return isinstance(obj, Parameter)

    def get_kind(self):
        kind = self._convert_arg_kind(str(self.obj.kind))
        kind |= 0 if self.obj.default is _empty else DEFAULT
        return kind

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
