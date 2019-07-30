#         Removing anything
#         Renaming keyword-arguments
#         Adding positional-arguments
#         Changing types (except where input types become generics)


def func1(a, d=None):
    return "nothing!"


def func2(a, b):  # type: (str, str) -> None
    return None


class MyClass1(object):
    pass
