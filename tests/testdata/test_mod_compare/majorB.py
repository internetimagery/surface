if False:
    from typing import *


def arg_rename(b):
    pass


def opt_arg_rename(a, c=""):
    pass


def arg_new(a, b):
    pass


def arg_gone(a):
    pass


def opt_arg_gone(a):
    pass


def var_arg_gone(a):
    pass


# def func_gone(a):
#     pass

# class ClassGone(object):
#     pass


class MethGone(object):
    pass
    # def method_gone(a):
    #     pass


# var_gone = "begone"

type_change = 123


def arg_type_change(a, b=0, *c):  # type: (bool, int, str) -> bool
    return True


def return_type_change_subtype():  # type: () -> Sequence[str]
    return []


class MethTypeChange(object):
    def meth_type_change(self, a, b=0, *c):  # type: (bool, int, str) -> bool
        return True
