if False:
    from typing import *


def rename_args_var(*a):
    pass


def rename_kwargs_var(**a):
    pass


class MethRenameVar(object):
    def rename_meth_args_var(self, *a):
        pass

    def rename_meth_kwargs_var(self, **a):
        pass


def add_new_types(a, b=None):
    pass


class _cause_fail(object):
    def __get__(*_):
        raise RuntimeError("ERROR")


class UnknownStays(object):
    unknown_stays = _cause_fail()


class MethChanges(object):
    def to_static(self, a):
        pass

    def to_class(self, a):
        pass

    @staticmethod
    def from_static(a):
        pass

    @classmethod
    def from_class(cls, a):
        pass

    @staticmethod
    def static_to_class(a):
        pass


def decorated(a):  # type: (int) -> None
    pass
