if False:
    from typing import *

new_var = 123


def new_func(a):
    pass


class NewClass(object):
    pass


class NewMeth(object):
    def new_method(a):
        pass


def new_kwarg_opt(a, b=None):
    pass


def new_arg_var(a, *b):
    pass


def new_kwarg_var(a, **b):
    pass


def change_arg_opt(a=0):  # type: (int) -> None
    pass


class NewMethArgs(object):
    def new_meth_kwarg_opt(self, a, b=None):
        pass

    def new_meth_arg_var(self, a, *b):
        pass

    def new_meth_kwarg_var(self, a, **b):
        pass

    def change_meth_arg_opt(a=0):  # type: (int) -> None
        pass


def type_changed(a):  # type: (Mapping[str, str]) -> Sequence[str]
    return []


class UnknownChange(object):
    ohno = "no error"
