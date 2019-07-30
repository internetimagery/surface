if False:
    import typing

var1 = 123
var2 = 456


def func1(a, b=42):
    """ Less boring function """
    return a + b


def func2(a):  # type: (typing.Sequence[str]) -> typing.Mapping[str, str]
    """ Characters n stuff """
    return {b: b for b in a}


def func3(a, *args, **kwargs):
    """ Multi item """
    return a + sum(args) + sum(kwargs.values())


def func4(a=43):  # type: (int) -> int
    """ positional / keyword / optional """
    return a


class Failer(object):
    ohno = "success"
    new_attr = "also success"


class NewClass(object):
    pass
