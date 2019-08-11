""" Wrap items in an immutable, simplified interface """

if False:  # type checking
    from typing import *

import collections


class Item(collections.Mapping):
    """ Wrap objects in a consistent traversal interface. """

    __slots__ = ("__item", "__parent", "__visitors")

    # ------------------------------------------
    # Internals
    # ------------------------------------------

    @property
    def item(self): # type: () -> Any
        """ Access interal object """
        return self.__item

    @property
    def parent(self): # type: () -> Any
        """ Get previous object """
        return self.__parent

    # ------------------------------------------
    # Building
    # ------------------------------------------

    @staticmethod
    def is_this_type(item, parent): # type: (Any, Optional[Item]) -> bool
        """ Check if the passed in object represents the Object """
        return False

    @classmethod
    def wrap(cls, visitors, item, parent=None): # type: (Sequence[Type[Item]], Any, Optional[Item]) -> Item
        """ Create an instance of Item, wrapping the provided object """
        for visitor in visitors:
            if visitor.is_this_type(item, parent):
                return visitor(visitors, item, parent)
        raise TypeError("Unhandled item {}".format(item))

    def __new__(cls, visitors, item, parent): # type: (Sequence[Type[Item]], Any, Optional[Item]) -> Item
        scope = super(Item, cls).__new__(cls)
        scope.__visitors = visitors
        scope.__item = item
        scope.__parent = parent # why is this not weak referenceable?
        return scope

    # ------------------------------------------
    # Traversing
    # ------------------------------------------

    def get_child(self, name): # type: (str) -> Any
        """ Return a child of this item """
        raise KeyError("Child {} not in {}".format(name, self.obj))

    def get_children_names(self): # type: () -> Sequence[Any]
        """ Return the names of all children in this item """
        return []

    def filter_name(self, name): # type: (str) -> bool
        """ Only allow names following the schema """
        return True

    # ------------------------------------------
    # Plumbing
    # ------------------------------------------

    def __len__(self):
        return len(list(self.__iter__()))

    def __iter__(self):
        return (name for name in self.get_children_names() if self.filter_name(name))

    def __getitem__(self, name):
        return self.wrap(self.__visitors, self.get_child(name), self)
