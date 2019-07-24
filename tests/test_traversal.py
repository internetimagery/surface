import sys
import os.path
import unittest

from surface._traversal import APITraversal, recurse
from surface._base import *

try:
    from importlib import reload
except ImportError:
    pass

path = os.path.join(os.path.dirname(__file__), "testdata")
sys.path.insert(0, path)


class TestRecurse(unittest.TestCase):
    def test_recurse(self):
        paths = recurse("test_mod_recurse")
        self.assertEqual(
            paths,
            [
                "test_mod_recurse",
                "test_mod_recurse.something",
                "test_mod_recurse.submodule",
                "test_mod_recurse.submodule.subsubmodule",
            ],
        )


class TestImporter(unittest.TestCase):

    maxDiff = None

    def test_basic(self):
        import test_mod_basic

        data = list(APITraversal().traverse(test_mod_basic))
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
                                Arg("c", "int", POSITIONAL | KEYWORD | DEFAULT),
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
                    "myModule",
                    "test_mod_basic.myModule",
                    (Var("myVar", "typing.List[int]"),),
                ),
                Var("myVar", "int"),
            ],
        )

    def test_err_attr(self):
        import test_mod_errors.errMethod as errMethod

        data = list(APITraversal().traverse(errMethod))
        self.assertEqual(
            data,
            [
                Class(
                    "Methods",
                    (
                        Unknown("err_method", "more like funtime error"),
                        Var("ok_method", "str"),
                    ),
                )
            ],
        )

    def test_err_attr(self):
        import test_mod_basic.cycleA as cycleA

        data = list(APITraversal().traverse(cycleA))
        self.assertEqual(
            data,
            [
                Class(
                    "CycleA",
                    (
                        Class(
                            "cycle",
                            (
                                Class(
                                    "cycle",
                                    (
                                        Unknown(
                                            "cycle",
                                            "Infinite Recursion: test_mod_basic.cycleA.CycleA.cycle",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
