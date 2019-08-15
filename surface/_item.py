""" Wrap items in an immutable, simplified interface """

if False:  # type checking
    from typing import *

    I = TypeVar("I", bound="Item")

import collections


class Item(collections.Mapping):
    """ Wrap objects in a consistent traversal interface. """

    __slots__ = ("__item", "__parent", "__visitors", "__children_names")

    # ------------------------------------------
    # Internals
    # ------------------------------------------

    @property
    def item(self):  # type: (Any) -> Any
        """ Access interal object """
        return self.__item

    @property
    def parent(self):  # type: (Any) -> I
        """ Get previous object """
        return self.__parent

    # ------------------------------------------
    # Building
    # ------------------------------------------

    @staticmethod
    def is_this_type(item, parent):  # type: (Any, Optional[I]) -> bool
        """ Check if the passed in object represents the Object """
        return False

    @classmethod
    def wrap(
        cls, visitors, item, parent=None
    ):  # type: (Sequence[Type[I]], Any, Optional[I]) -> I
        """ Create an instance of Item, wrapping the provided object """
        for visitor in visitors:
            if visitor.is_this_type(item, parent):
                return visitor(visitors, item, parent)
        raise TypeError("Unhandled item {}".format(item))

    def __new__(
        cls, visitors, item, parent
    ):  # type: (Sequence[Type[I]], Any, Optional[I]) -> I
        scope = super(Item, cls).__new__(cls)
        scope.__visitors = visitors
        scope.__item = item
        scope.__parent = parent  # why is this not weak referenceable?
        scope.__children_names = None
        return scope

    # ------------------------------------------
    # Traversing
    # ------------------------------------------

    def get_child(self, name):  # type: (str) -> Any
        """ Return a child of this item """
        raise KeyError("Child {} not in {}".format(name, self.item))

    def get_children_names(self):  # type: () -> Sequence[str]
        """ Return the names of all children in this item """
        return []

    # ------------------------------------------
    # Plumbing
    # ------------------------------------------

    def __len__(self):
        return len(list(self.__iter__()))

    def __iter__(self):
        if self.__children_names is None:
            self.__children_names = tuple(self.get_children_names())
        return iter(self.__children_names)

    def __getitem__(self, name):
        return self.wrap(self.__visitors, self.get_child(name), self)
