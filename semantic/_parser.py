""" Parse AST into base types """

import ast
from abc import ABCMeta, abstractmethod
from semantic._base import ANY, MODULE, Var

if 0:
    from typing import Iterator

__all__ = ["parse"]

IGNORED_MODULES = ["typing"]


def parse(source):  # type: (str) -> Iterator[Any]
    module = ast.parse(source)
    for node in module.body:
        parser = node_parse_map.get(type(node))
        if parser:
            for item in parser(node):
                yield item


def parse_import(node):  # type: (ast.Import) -> Iterator[Var]
    for name in node.names:
        var_name = name.asname or name.name
        if valid_name(var_name) and var_name not in IGNORED_MODULES:
            yield Var(var_name, MODULE)


def parse_import_from(node):  # type: (ast.ImportFrom) -> Iterator[Var]
    if node.module in IGNORED_MODULES:
        return
    for name in node.names:
        var_name = name.asname or name.name
        if valid_name(var_name):
            yield Var(var_name, MODULE)


def parse_assign(node):  # type: (ast.Assign) -> Iterator[Var]
    for var_node in node.targets:
        if isinstance(var_node, ast.Name):
            var_name = var_node.id
            if valid_name(var_name):
                yield Var(var_name, ANY)
        else:
            for var_node, var_value in zip(iter_node(var_node), iter_node(node.value)):
                if isinstance(var_node, ast.Name):
                    var_name = var_node.id
                    if valid_name(var_name):
                        yield Var(var_name, ANY)


# Utilities


def valid_name(name):  # type: (str) -> bool
    return not name.startswith("_")


def iter_node(node):  # type: (Any) -> Iterator[Any]
    if isinstance(node, (ast.Tuple, ast.List)):
        return node.elts
    if isinstance(node, ast.Dict):
        return node.keys
    return []


node_parse_map = {
    ast.Import: parse_import,
    ast.ImportFrom: parse_import_from,
    ast.Assign: parse_assign,
}
