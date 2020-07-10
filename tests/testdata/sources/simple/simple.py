class SimpleClass(object):
    def simple_method(self, name):
        "A simple method!"
        name = name.capitalize()
        return "person " + name

    @classmethod
    def simple_class_method(cls, name):
        "A simple class method!"
        name = name.capitalize()
        return "person " + name


def simple_function(name):
    return "cat"
