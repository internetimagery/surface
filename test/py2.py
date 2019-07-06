import unittest
from semantic._parser_py2 import get_api
from semantic._base import *


class TestParse(unittest.TestCase):
    def test_import(self):
        code = """
import abcd
from typing import List
import _abc
from abcd import _efgh
from abcd import efgh, ijkl
from abcd import *
"""
        data = list(get_api(code))
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
        code = """
abcd = "123"
efgh = 123
ijkl, mnop = 456, 789
qrst, = {"123": 123}
[uvwx] = [123]
uvw.xyz = True
index[0] = 123
"""
        data = list(get_api(code))
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
        code = """
def func1(a, b, c): pass
def func2(a, b=None): pass
@decoration
def func3(a, *args, **kwargs): pass
"""
        data = list(get_api(code))
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
                    "func3",
                    (Arg("a", ANY, False), Arg("*", ANY, False), Arg("**", ANY, True)),
                    ANY,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
