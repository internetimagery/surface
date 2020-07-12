
from typing import Any, Dict, Optional

import ast
import contextlib

from surface.compare._representation import BaseRepresentation, Reference, Class, Function

VARIABLE = (123, 456)

class RepresentationBuilder(ast.NodeVisitor):
    """ Walk module, build representation of important elements """

    def __init__(self, module_name: str) -> None:
        self._stack = [module_name]
        self._aliases: Dict[str, str] = {}
        self._representation: Dict[str, BaseRepresentation] = {}

    def get_representation(self) -> Dict[str, Any]:
        return self._representation

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for name in node.names:
            with self._scope(name.asname or name.name):
                self._add(Reference(node))
    
    def visit_Import(self, node: ast.Import) -> None:
        for name in node.names:
            with self._scope(name.asname or name.name):
                self._add(Reference(node))
    
    #def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
    #    source = self._name(node.target)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        with self._scope(node.name):
            self._add(Class(node))
            self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        with self._scope(node.name):
            self._add(Function(node))

    def _name(self, node: str) -> str:
        if isinstance(node, ast.Name):
            return node.id
        raise RuntimeError("No name {}".format(node))

    def _alias(self, source: str, target: str) -> None:
        path = ".".join(self._stack)
        self._aliases["{}.{}".join(path, source)] = "{}.{}".join(path, target)
    
    def _add(self, rep: BaseRepresentation, path: Optional[str] = None) -> None:
        if not path:
            path = ".".join(self._stack)
        self._representation[path] = rep
    
    @contextlib.contextmanager
    def _scope(self, name: str) -> None:
        self._stack.append(name)
        try:
            yield
        finally:
            self._stack.pop()


if __name__ == "__main__":
    import os, pprint

    with open(__file__) as fh:
        module = ast.parse(fh.read())
        rep = RepresentationBuilder("module")
        rep.visit(module)
        pprint.pprint(rep.get_representation())