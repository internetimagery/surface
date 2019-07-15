
import sys
import os.path
import unittest
from typing import Any


from surface._traversal import traverse
from surface._base import *

try:
    from importlib import reload
except ImportError:
    pass

path = os.path.join(os.path.dirname(__file__), "testdata")
sys.path.insert(0, path)
import test_mod_basic

class TestImporter(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        reload(test_mod_basic)

    def test_basic(self):
        data = list(traverse(test_mod_basic))
        self.assertEqual(
            data,
            [
                Class(
                    "myClass",
                    (
                        Func(
                            "myMethod",
                            (
                                Arg("a", Any, POSITIONAL | KEYWORD),
                                Arg("b", Any, POSITIONAL | KEYWORD),
                                Arg("c", Any, POSITIONAL | KEYWORD | DEFAULT),
                            ),
                            Any,
                        ),
                        Func(
                            "myStatic",
                            (
                                Arg("a", Any, POSITIONAL | KEYWORD),
                                Arg("b", Any, POSITIONAL | KEYWORD),
                                Arg("c", Any, POSITIONAL | VARIADIC),
                            ),
                            Any,
                        ),
                    ),
                ),
                Func(
                    "myFunc",
                    (
                        Arg("a", Any, POSITIONAL | KEYWORD),
                        Arg("b", Any, POSITIONAL | KEYWORD),
                        Arg("c", Any, KEYWORD | VARIADIC),
                    ),
                    Any,
                ),
                Func(
                    "myLambda",
                    (
                        Arg("x", Any, POSITIONAL | KEYWORD),
                    ),
                    Any,
                ),
                Var("myVar", Any),
            ])



if __name__ == '__main__':
    unittest.main()
