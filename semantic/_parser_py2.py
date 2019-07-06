""" Parse AST into base types """

import ast
from itertools import izip
from abc import ABCMeta, abstractmethod
from semantic._base import *

if 0:
    from typing import Iterator

__all__ = ["parse"]

IGNORED_MODULES = ["typing"]
VALID_NAMES = ["__init__"]


def get_api(module):  # type: (ast.Module) -> Iterator[Any]
    """ Collect the exposed API of the source file """
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
        if var_name == "*":
            yield Ref(node.module)
        elif valid_name(var_name):
            yield Var(var_name, MODULE)


def parse_assign(node):  # type: (ast.Assign) -> Iterator[Var]
    for var_node in node.targets:
        # Straight assignment eg: my_var = 123
        if isinstance(var_node, ast.Name):
            var_name = var_node.id
            if valid_name(var_name):
                yield Var(var_name, ANY)
        else:
            # Multi assignment eg: my_var1, my_var2 = 1, 2
            for var_node, var_value in izip(iter_node(var_node), iter_node(node.value)):
                if isinstance(var_node, ast.Name):
                    var_name = var_node.id
                    if valid_name(var_name):
                        yield Var(var_name, ANY)


def parse_func(node):  # type: (ast.FunctionDef) -> Iterator[Func]
    if not valid_name(node.name):
        return
    defaults_pos = len(node.args.args) - len(node.args.defaults)
    args = tuple(
        Arg(arg.id, ANY, i >= defaults_pos) for i, arg in enumerate(node.args.args)
    )
    if node.args.vararg:
        args += (Arg("*", ANY, False),)
    if node.args.kwarg:
        args += (Arg("**", ANY, True),)
    yield Func(node.name, args, ANY)


def parse_class(node):  # type: (asf.ClassDef) -> Iterator[Class]
    if not valid_name(node.name):
        return
    body = tuple(get_api(node))
    yield Class(node.name, body)


node_parse_map = {
    ast.Import: parse_import,
    ast.ImportFrom: parse_import_from,
    ast.Assign: parse_assign,
    ast.FunctionDef: parse_func,
    ast.ClassDef: parse_class,
}

# Utilities


def valid_name(name):  # type: (str) -> bool
    if name in VALID_NAMES:
        return True
    return not name.startswith("_")


def iter_node(node):  # type: (Any) -> Iterator[Any]
    if isinstance(node, (ast.Tuple, ast.List)):
        return node.elts
    if isinstance(node, ast.Dict):
        return node.keys
    return []
