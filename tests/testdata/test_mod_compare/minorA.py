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


def func4(a):  # type: (int) -> int
    """ positional / keyword """
    return a


class _FAIL(object):
    def __get__(self, *_):
        raise RuntimeError("CANT GET THIS")


class Failer(object):
    ohno = _FAIL()
