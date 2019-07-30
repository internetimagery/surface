#         Adding new variables, functions, classes, modules, optional-keyword-arguments, *args, **kwargs
#         Changing positional-only-argument to include keyword
#         Changing input types to be generics, eg: List to Sequence, Dict to Mapping etc
#         Unable to verify the change (ie attribute access failed / recursive object)

if False:
    import typing

var1 = 123


def func1(a):
    """ Boring function """
    return a


def func2(a):  # type: (typing.List[str]) -> typing.Dict[str, str]
    """ Characters n stuff """
    return {b: b for b in a}


def func3(a):
    """ Single item """
    return a


class _FAIL(object):
    def __get__(self, *_):
        raise RuntimeError("CANT GET THIS")


class Failer(object):
    ohno = _FAIL()
