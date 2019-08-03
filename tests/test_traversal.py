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
if path not in sys.path:
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
                                Arg("a", UNKNOWN, POSITIONAL | KEYWORD),
                                Arg("b", UNKNOWN, POSITIONAL | KEYWORD),
                                Arg("c", "int", POSITIONAL | KEYWORD | DEFAULT),
                            ),
                            UNKNOWN,
                        ),
                        Func(
                            "myStatic",
                            (
                                Arg("a", UNKNOWN, POSITIONAL | KEYWORD),
                                Arg("b", UNKNOWN, POSITIONAL | KEYWORD),
                                Arg("c", UNKNOWN, POSITIONAL | VARIADIC),
                            ),
                            UNKNOWN,
                        ),
                    ),
                ),
                Func(
                    "myFunc",
                    (
                        Arg("a", UNKNOWN, POSITIONAL | KEYWORD),
                        Arg("b", UNKNOWN, POSITIONAL | KEYWORD),
                        Arg("c", UNKNOWN, KEYWORD | VARIADIC),
                    ),
                    UNKNOWN,
                ),
                Func("myLambda", (Arg("x", UNKNOWN, POSITIONAL | KEYWORD),), UNKNOWN),
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
                                Unknown(
                                    "cycle",
                                    "Circular Reference: <class 'test_mod_basic.cycleA.CycleA'>",
                                ),
                            ),
                        ),
                    ),
                )
            ],
        )

    def test_stdlib(self):
        # Run through standard lib to see if anything breaks
        modules = sys.builtin_module_names
        for module in modules:
            data = list(APITraversal().traverse(module))
            self.assertTrue(len(data))


if __name__ == "__main__":
    unittest.main()
