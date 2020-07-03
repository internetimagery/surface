""" Build representational information from live objects """

from typing import NamedTuple

import re

INDENT = "    "

# Name format package.module:Class.method
name_split = re.compile(r"[\.:]").split

def get_indent(num):
    # type: (int) -> str
    return INDENT * num

Import = NamedTuple("Import", [("path", str), ("name", str), ("alias", str)])


class BaseWrapper(object):

    def __init__(self, wrapped):
        # type: (Any) -> None
        """ Pull information from a live object to create a representation later """
        self._id = id(wrapped)
    
    def get_id(self):
        # type: () -> int
        """ Ye olde ID """
        return self._id
    
    def get_imports(self, name):
        # type: (str) -> List[Import]
        """ Any imports required to be added for this. """
        return []
    
    def get_body(self, indent, name):
        # type: (int, str) -> str
        """ Export the representaton as a string suitable for insertion into a stubfile """
        return ""


class Module(BaseWrapper):

    def __init__(self, module):
        # type: (types.ModuleType) -> None
        super(Module, self).__init__(module)
        self._name = module.__name__

    def get_name(self):
        # type: () -> str
        return self._name
    
    def get_imports(self, name):
        # type: (str) -> List[Import]

        if name == self._name:
            # We are imported by our full name.
            # eg:
            # - import module
            # - import package.module
            return [Import(name, "", "")]
        module_parts = self._name.rsplit(".", -1)
        if name == module_parts[-1]:
            # We are imported by module name from a package
            # eg:
            # - from package import module
            return [Import(module_parts[0], name, "")]
        # We must be imported and given an alias.
        # eg:
        # - import module as _alias
        # - from package import module as _alias
        if len(module_parts) == 1:
            return [Import(module_parts[0], "", name)]
        return [Import(module_parts[0], module_parts[-1], name)]

class Class(BaseWrapper):

    def get_body(self, indent, name):
        # TODO: get mro for subclasses
        # TODO: represent as an attribute if name does not originate (ie not definition)
        return '{}class {}(object):\n{}""" CLASSY """'.format(get_indent(indent), name_split(name)[-1], get_indent(indent+1))

class Function(BaseWrapper):

    def get_body(self, indent, name):
        # TODO: get signature information
        return "{}def {}(): ...".format(get_indent(indent), name_split(name)[-1])

class Method(Function):
    pass

class ClassMethod(Function):
    pass

class StaticMethod(Function):
    pass

class Attribute(BaseWrapper):

    def get_body(self, indent, name):
        return "{}{}: Any = ...".format(get_indent(indent), name_split(name)[-1])