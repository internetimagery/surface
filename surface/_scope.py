""" Scope """

if False:  # type checking
    from typing import *

import sys
import traceback
import collections

import logging

LOG = logging.getLogger(__name__)


class Scope(collections.Mapping):
    """ Represent objects as graph of containers. """

    __slots__ = ("obj", "name", "parent")

    NAME_FILTER = staticmethod(lambda n: not n.startswith("_"))

    # ------------------------------------------
    # Building
    # ------------------------------------------

    @classmethod
    def wrap(cls, obj, name="", parent=None): # type: (Any, str, Optional[Any]) -> Any
        """ Entry point to create a scope """
        for handler in cls._get_handlers(Scope):
            if handler.is_this_type(obj, name, parent):
                return handler(obj, name, parent)
        return Scope(obj, name, parent) # Plain scope as fallback

    def __new__(cls, obj, name="", parent=None): # type: (Any, str, Dict[str, Any]) -> None
        scope = super(Scope, cls).__new__(cls)
        scope.obj = obj
        scope.name = name
        scope.parent = parent # why is this not weak referenceable?
        return scope

    def is_this_type(obj, name, parent): # type: (Any, str, Any) -> bool
        """ Check if the passed in object represents the scope """
        return False

    # ------------------------------------------
    # Traversing
    # ------------------------------------------

    def get_child(self, name): # type: (str) -> Any
        raise KeyError("Child {} not in {}".format(name, self.obj))

    def get_children_names(self): # type: () -> Sequence[Any]
        return []

    # ------------------------------------------
    # Plumbing
    # ------------------------------------------

    @staticmethod
    def _get_handlers(cls): # type: (Type[Scope]) -> Set[Any]
        handlers = set([cls])
        stack = list(cls.__subclasses__())
        while stack:
            handler = stack.pop()
            if handler not in handlers:
                handlers.add(handler)
                stack.extend(handler.__subclasses__())
        return handlers

    def __len__(self):
        return len(list(self.__iter__()))

    def __iter__(self):
        return (name for name in self.get_children_names() if self.NAME_FILTER(name))

    def __getitem__(self, name):
        try:
            value = self.get_child(name)
        except KeyError:
            raise
        except Exception:
            return ErrorScope(name, parent=self)
        else:
            return self.wrap(value, name, self)


class ErrorScope(Scope):
    """ Special scope to represent errors from unreachable objects. """

    __slots__ = ("type", "trace")

    def __new__(cls, name, parent=None):
        err = sys.last_value
        scope = super(ErrorScope, cls).__new__(cls, err, name, parent)
        scope.type = sys.last_type
        scope.trace = traceback.format_exc()
        LOG.debug(scope.trace) # Alert us of this error
        return scope
