""" Wrapping static ast objects """

if False:  # type checking
    from typing import *

    A = TypeVar("A", bound="AstItem")

import ast
import collections

from surface._base import UNKNOWN, PY2
from surface._item import Item


class AstItem(Item):

    wraps = None  # type: Any

    __slots__ = []  # type: ignore

    @classmethod
    def parse(cls, visitors, source):  # type: (Sequence[Type[A]], str) -> A
        module = ast.parse(source)
        return cls.wrap(visitors, module)

    @classmethod
    def is_this_type(cls, item, parent):  # type: (A, A) -> bool
        return isinstance(item, cls.wraps)


class ModuleAst(AstItem):

    wraps = ast.Module

    def get_children_names(self):
        return range(len(self.item.body))

    def get_child(self, index):
        return self.item.body[index].value


class SliceAst(AstItem):

    wraps = (ast.Index, ast.Slice, ast.ExtSlice)

    def get_children_names(self):
        return range(len(self._children()))

    def get_child(self, index):
        return self._children()[index]

    def _children(self):
        if isinstance(self.item, ast.Index):
            return [self.item.value]
        if isinstance(self.item, ast.ExtSlice):
            return self.item.dims
        children = []
        if self.item.lower:
            children.append(self.item.lower)
        if self.item.upper:
            children.append(self.item.upper)
        if self.item.step:
            children.append(self.item.step)
        return children


class TupleAst(AstItem):

    wraps = ast.Tuple

    def get_children_names(self):
        return range(len(self.item.elts))

    def get_child(self, index):
        return self.item.elts[index]


class NameAst(AstItem):

    if PY2:
        wraps = (ast.Name, ast.Attribute, ast.Subscript)
    else:
        wraps = (ast.Name, ast.Attribute, ast.Subscript, ast.NameConstant)

    @property
    def name(self):
        if isinstance(self.item, ast.Name):
            return self.item.id
        if isinstance(self.item, ast.Attribute):
            return ".".join(reversed(self._walk(self.item)))
        if isinstance(self.item, ast.Subscript):
            return ".".join(reversed(self._walk(self.item.value)))
        return repr(self.item.value)

    def get_children_names(self):
        if isinstance(self.item, ast.Subscript):
            return [0]
        return []

    def get_child(self, index):
        if index == 0 and isinstance(self.item, ast.Subscript):
            return self.item.slice
        raise KeyError("Index {} is not here.".format(index))

    def _walk(self, item, chain=None):
        if chain is None:
            chain = []
        if isinstance(item, ast.Attribute):
            chain.append(item.attr)
            self._walk(item.value, chain)
        elif isinstance(item, ast.Name):
            chain.append(item.id)
        else:
            raise TypeError("API.Unknown type {}".format(item))
        return chain


class EllipsisAst(AstItem):

    wraps = ast.Ellipsis


class UnknownAst(AstItem):
    @staticmethod
    def is_this_type(item, parent):
        return (
            isinstance(item, ast.UnaryOp)
            and isinstance(item.op, ast.Invert)
            and isinstance(item.operand, ast.Name)
            and item.operand.id == UNKNOWN[1:]
        )
