from functools import wraps
from typing import List

variable1: List[str] = []


class Obj1(object):
    attr1: List[int] = []


def func1(a: int, b: str = "") -> bool:
    return a == str(b)


def func2(a: func1, b: List[str] = None) -> List[bool]:
    return [a(c, d) for c, d in enumerate(b)]


def func3(a: Obj1) -> bool:
    return isinstance(a, Obj1)


def wrap(func):
    @wraps(func)  # Required to find the source functions annotations fully
    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    return inner


@wrap
def func4(a: int, b: str) -> bool:
    return True
