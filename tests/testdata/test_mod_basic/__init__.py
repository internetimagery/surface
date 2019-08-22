import test_mod_basic.myModule as myModule

__all__ = ("myVar", "myFunc")

myVar = 123

myLambda = lambda x: x + 1


def myFunc(a, b, **c):
    return a + b + c


class myClass(object):
    def myMethod(self, a, b, c=1):
        return a + b + c

    @staticmethod
    def myStatic(a, b, *c):
        return a + b + c

    myVar = 123

    @property
    def myProp(self):  # type: () -> int
        return 123
