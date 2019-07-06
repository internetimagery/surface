import ast
import unittest
from semantic._parser_py2 import get_api
from semantic._base import *


class TestParse(unittest.TestCase):
    def test_import(self):
        module = ast.parse(
            """
import abcd
from typing import List
import _abc
from abcd import _efgh
from abcd import efgh, ijkl
from abcd import *
"""
        )
        data = list(get_api(module))
        self.assertEqual(
            data,
            [
                Var("abcd", MODULE),
                Var("efgh", MODULE),
                Var("ijkl", MODULE),
                Ref("abcd"),
            ],
        )

    def test_variable(self):
        module = ast.parse(
            """
abcd = "123"
efgh = 123
ijkl, mnop = 456, 789
qrst, = {"123": 123}
[uvwx] = [123]
uvw.xyz = True
index[0] = 123
"""
        )
        data = list(get_api(module))
        self.assertEqual(
            data,
            [
                Var("abcd", ANY),
                Var("efgh", ANY),
                Var("ijkl", ANY),
                Var("mnop", ANY),
                Var("qrst", ANY),
                Var("uvwx", ANY),
            ],
        )

    def test_function(self):
        module = ast.parse(
            """
def func1(a, b, c): pass
def func2(a, b=None): pass
def _func3(a, b, c): pass
@decoration
def func4(a, *args, **kwargs): pass
"""
        )
        data = list(get_api(module))
        self.assertEqual(
            data,
            [
                Func(
                    "func1",
                    (Arg("a", ANY, False), Arg("b", ANY, False), Arg("c", ANY, False)),
                    ANY,
                ),
                Func("func2", (Arg("a", ANY, False), Arg("b", ANY, True)), ANY),
                Func(
                    "func4",
                    (Arg("a", ANY, False), Arg("*", ANY, False), Arg("**", ANY, True)),
                    ANY,
                ),
            ],
        )

    def test_class(self):
        module = ast.parse(
            """
class MyClass(object):
    var = 123
    def __init__(self, a, b, c): pass
    @classmethod
    def func1(cls, a, b, c): pass
    @staticmethod
    def func2(a, b, c): pass
    def _func3(self, a, b, c): pass
"""
        )
        data = list(get_api(module))
        self.assertEqual(
            data,
            [
                Class(
                    "MyClass",
                    (
                        Var("var", ANY),
                        Func(
                            "__init__",
                            (
                                Arg("a", ANY, False),
                                Arg("b", ANY, False),
                                Arg("c", ANY, False),
                            ),
                            ANY,
                        ),
                        Func(
                            "func1",
                            (
                                Arg("a", ANY, False),
                                Arg("b", ANY, False),
                                Arg("c", ANY, False),
                            ),
                            ANY,
                        ),
                        Func(
                            "func2",
                            (
                                Arg("a", ANY, False),
                                Arg("b", ANY, False),
                                Arg("c", ANY, False),
                            ),
                            ANY,
                        ),
                    ),
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
