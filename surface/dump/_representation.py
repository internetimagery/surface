""" Build representational information from live objects """

class BaseWrapper(object):

    def __init__(self, wrapped):
        # type: (Any) -> None
        pass
    
    def export(self, name):
        # type: (str) -> str
        return ""

class Module(BaseWrapper):
    pass

class Class(BaseWrapper):
    pass

class Function(BaseWrapper):
    pass

class Method(Function):
    pass

class ClassMethod(Function):
    pass

class StaticMethod(Function):
    pass

class Attribute(BaseWrapper):

    def export(self, name):
        return "{}: Any = ...".format(name)