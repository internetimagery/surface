""" Build representational information from live objects """

import re

# Name format package.module:Class.method
name_split = re.compile(r"[\.:]").split


class BaseWrapper(object):

    def __init__(self, wrapped):
        # type: (Any) -> None
        """ Pull information from a live object to create a representation later """
        self._id = id(wrapped)
    
    def get_id(self):
        # type: () -> int
        """ Ye olde ID """
        return self._id
    
    def get_dependencies(self):
        # type: () -> List[str]
        """ Provide a list of dependencies that will need to be added as imports """
    
    def export(self, indent, name):
        # type: (str, str) -> str
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

    def export(self, indent, name):
        return "# An import goes here, to {}".format(name)

class Class(BaseWrapper):

    def export(self, indent, name):
        # TODO: get mro for subclasses
        # TODO: represent as an attribute if name does not originate
        return "{}class {}(object): ...".format(indent, name_split(name)[-1])

class Function(BaseWrapper):

    def export(self, indent, name):
        # TODO: get signature information
        return "{}def {}(): ...".format(indent, name_split(name)[-1])

class Method(Function):
    pass

class ClassMethod(Function):
    pass

class StaticMethod(Function):
    pass

class Attribute(BaseWrapper):

    def export(self, indent, name):
        return "{}{}: Any = ...".format(indent, name_split(name)[-1])