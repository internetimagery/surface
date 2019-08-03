if False:
    from typing import *


def arg_rename(a):
    pass


def opt_arg_rename(a, b=""):
    pass


def arg_new(a):
    pass


def arg_gone(a, b):
    pass


def opt_arg_gone(a, b=None):
    pass


def var_arg_gone(a, *b):
    pass


def func_gone(a):
    pass


class ClassGone(object):
    pass


class MethGone(object):
    def method_gone(a):
        pass


var_gone = "begone"

type_change = "123"


def arg_type_change(a, b="", *c):  # type: (int, str, bool) -> int
    return 0


def return_type_change_subtype():  # type: () -> List[str]
    return []


class MethTypeChange(object):
    def meth_type_change(self, a, b="", *c):  # type: (int, str, bool) -> int
        return 0
