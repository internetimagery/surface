if False:
    from typing import *

# new_var = 123

# def new_func(a):
#     pass

# class NewClass(object):
#     pass


class NewMeth(object):
    pass


def new_kwarg_opt(a):
    pass


def new_arg_var(a):
    pass


def new_kwarg_var(a):
    pass


def change_arg_opt(a):  # type: (int) -> None
    pass


class NewMethArgs(object):
    def new_meth_kwarg_opt(self, a):
        pass

    def new_meth_arg_var(self, a):
        pass

    def new_meth_kwarg_var(self, a):
        pass

    def change_meth_arg_opt(self, a):  # type: (int) -> None
        pass


def type_changed(a):  # type: (Dict[str, str]) -> List[str]
    return []


class _make_error(object):
    def __get__(self, *_):
        raise RuntimeError("ERROR")


class UnknownChange(object):
    ohno = _make_error()
