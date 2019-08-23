""" Wrapping static ast objects """

import ast
import collections

from surface._base import UNKNOWN
from surface._item import Item
from surface._utils import get_tokens

# TODO: Once this is done. This can be reused in the comment parsing functionality.


class TokenMap(collections.namedtuple("TokenMap", ("stream", "index"))):
    """ Map token stream to its positional information """

    def __new__(cls, source):
        stream = get_tokens(source) or []
        index = {tok[2]: i for i, tok in enumerate(stream)}
        return super(TokenMap, cls).__new__(cls, stream, index)

    def __bool__(self):
        return bool(self.stream)

    __nonzero__ = __bool__


class AstItem(Item):
    # TODO: add a parse method that passes in source and generates ast + mapping
    # TODO: override wrap, to also send the mapping info to any child classes
    __slots__ = ["_mapping"]

    @classmethod
    def parse(cls, visitors, source):
        module = ast.parse(source)
        inst = cls.wrap(visitors, module)
        inst._mapping = TokenMap(source)
        return inst

    @classmethod
    def wrap(cls, visitors, item, parent=None):
        inst = super(AstItem, cls).wrap(visitors, item, parent)
        if parent is not None:
            inst._mapping = parent._mapping
        return inst


class ModuleAst(AstItem):
    @staticmethod
    def is_this_type(item, parent):
        return isinstance(item, ast.Module)

    def get_children_names(self):
        return range(len(self.item.body))

    def get_child(self, index):
        return self.item.body[index].value


class SubscriptAst(AstItem):
    @staticmethod
    def is_this_type(item, parent):
        return isinstance(item, ast.Subscript)

    def get_children_names(self):
        return [0, 1]

    def get_child(self, index):
        if index is 0:
            return self.item.value
        elif index is 1:
            return self.item.slice.value
        else:
            raise KeyError("Index {} is not here.".format(index))


class TupleAst(AstItem):
    @staticmethod
    def is_this_type(item, parent):
        return isinstance(item, ast.Tuple)

    def get_children_names(self):
        return range(len(self.item.elts))

    def get_child(self, index):
        return self.item.elts[index]


class AttributeAst(AstItem):
    @staticmethod
    def is_this_type(item, parent):
        return isinstance(item, ast.Attribute)

    @property
    def name(self):
        return ".".join(reversed(self._walk(self.item)))

    def _walk(self, item, chain=None):
        if chain is None:
            chain = []
        if isinstance(item, ast.Attribute):
            chain.append(item.attr)
            self._walk(item.value, chain)
        elif isinstance(item, ast.Name):
            chain.append(item.id)
        else:
            raise TypeError("Unknown type {}".format(item))
        return chain


class NameAst(AstItem):
    @staticmethod
    def is_this_type(item, parent):
        return isinstance(item, ast.Name)

    @property
    def name(self):
        return self.item.id


class UnknownAst(AstItem):
    @staticmethod
    def is_this_type(item, parent):
        return (
            isinstance(item, ast.UnaryOp)
            and isinstance(item.op, ast.Invert)
            and isinstance(item.operand, ast.Name)
            and item.operand.id == UNKNOWN[1:]
        )


if __name__ == "__main__":
    typestring = "typing.Dict[str, typing.List[~unknown]]"

    visitors = [ModuleAst, SubscriptAst, NameAst, TupleAst, UnknownAst, AttributeAst]

    p = AstItem.parse(visitors, typestring)

    def walk(item):
        print(item, getattr(item, "name", ""))
        for child in item.values():
            walk(child)

    walk(p)
