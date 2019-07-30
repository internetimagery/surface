#         Adding new variables, functions, classes, modules, optional-keyword-arguments, *args, **kwargs
#         Changing positional-only-argument to include keyword
#         Changing input types to be generics, eg: List to Sequence, Dict to Mapping etc
#         Unable to verify the change (ie attribute access failed / recursive object)

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


class Failer(object):
    ohno = "success"
    new_attr = "also success"


class NewClass(object):
    pass
