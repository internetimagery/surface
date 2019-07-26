from typing import List


class Obj(object):
    pass


def func1(a: int, b: str = "") -> bool:
    return a == str(b)


def func2(a: func1, b: List[str] = None) -> List[bool]:
    return [a(c, d) for c, d in enumerate(b)]


def func3(a: Obj) -> bool:
    return isinstance(a, Obj)
