from typing import List

variable1: List[str] = []


class Obj1(object):
    attr1: List[int] = []


def func1(a: int, b: str = "") -> bool:
    return a == str(b)


def func2(a: func1, b: List[str] = None) -> List[bool]:
    return [a(c, d) for c, d in enumerate(b)]


def func3(a: Obj1) -> bool:
    return isinstance(a, Obj)
