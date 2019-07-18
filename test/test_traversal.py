import sys
import os.path
import unittest

from surface._traversal import traverse, recurse
from surface._base import *

try:
    from importlib import reload
except ImportError:
    pass

path = os.path.join(os.path.dirname(__file__), "testdata")
sys.path.insert(0, path)
import test_mod_basic


class TestRecurse(unittest.TestCase):

    def test_recurse(self):
        paths = recurse("test_mod_recurse")
        print("PATHS", paths)
        self.assertEqual(paths, [
            "test_mod_recurse",
            "test_mod_recurse.something",
            "test_mod_recurse.submodule",
            "test_mod_recurse.submodule.subsubmodule",
        ])


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
                                Arg("a", "typing.Any", POSITIONAL | KEYWORD),
                                Arg("b", "typing.Any", POSITIONAL | KEYWORD),
                                Arg("c", "typing.Any", POSITIONAL | KEYWORD | DEFAULT),
                            ),
                            "typing.Any",
                        ),
                        Func(
                            "myStatic",
                            (
                                Arg("a", "typing.Any", POSITIONAL | KEYWORD),
                                Arg("b", "typing.Any", POSITIONAL | KEYWORD),
                                Arg("c", "typing.Any", POSITIONAL | VARIADIC),
                            ),
                            "typing.Any",
                        ),
                    ),
                ),
                Func(
                    "myFunc",
                    (
                        Arg("a", "typing.Any", POSITIONAL | KEYWORD),
                        Arg("b", "typing.Any", POSITIONAL | KEYWORD),
                        Arg("c", "typing.Any", KEYWORD | VARIADIC),
                    ),
                    "typing.Any",
                ),
                Func(
                    "myLambda",
                    (Arg("x", "typing.Any", POSITIONAL | KEYWORD),),
                    "typing.Any",
                ),
                Module(
                    "myModule", "test_mod_basic.myModule", (Var("myVar", "typing.Any"),)
                ),
                Var("myVar", "typing.Any"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
