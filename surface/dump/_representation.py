""" Build representational information from live objects """

class BaseWrapper(object):

    def __init__(self, object_):
        self.wrapped = object_
    
    def export(self):
        return ""

class Module(BaseWrapper):
    pass

class Class(BaseWrapper):
    pass

class Function(BaseWrapper):
    pass

class Method(BaseWrapper):
    pass

class ClassMethod(BaseWrapper):
    pass

class StaticMethod(BaseWrapper):
    pass

class Attribute(BaseWrapper):
    pass