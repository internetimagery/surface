#         Removing anything
#         Renaming keyword-arguments
#         Adding positional-arguments
#         Changing types (except where input types become generics)

var1 = "begone"


def func1(a, b, c=None):
    return "nothing!"


def func2(a, b):  # type: (int, str) -> None
    return None


def func3(a):
    return "OK"


class MyClass1(object):
    def myMethod(self, a):
        return "Nothing"


class MyClass2(object):
    pass
