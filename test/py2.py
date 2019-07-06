import unittest
from semantic._parser import parse
from semantic._base import ANY, MODULE, Var


class TestParse(unittest.TestCase):
    def test_import(self):
        code = """
import abcd
from typing import List
import _abc
from abcd import _efgh
from abcd import efgh, ijkl
"""
        data = list(parse(code))
        self.assertEqual(
            data, [Var("abcd", MODULE), Var("efgh", MODULE), Var("ijkl", MODULE)]
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
        data = list(parse(code))
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


if __name__ == "__main__":
    unittest.main()
