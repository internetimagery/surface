#         Removing anything
#         Renaming keyword-arguments
#         Adding positional-arguments
#         Changing types (except where input types become generics)


def func1(a):
    return "nothing!"


def func2(a, b):  # type: (str, str) -> None
    return None


def func4(c=None):
    return 123


class MyClass1(object):
    pass
