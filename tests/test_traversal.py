import sys
import os.path
import unittest

from surface import get_api
from surface._traversal import Traversal, recurse
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

        data = Traversal().traverse(test_mod_basic)
        self.assertEqual(
            data,
            Module(
                "test_mod_basic",
                "test_mod_basic",
                (
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
                    Func(
                        "myLambda", (Arg("x", UNKNOWN, POSITIONAL | KEYWORD),), UNKNOWN
                    ),
                    Module(
                        "myModule",
                        "test_mod_basic.myModule",
                        (Var("myVar", "typing.List[int]"),),
                    ),
                    Var("myVar", "int"),
                ),
            ),
        )

    def test_depth(self):
        import test_mod_basic

        data = Traversal(depth=0).traverse(test_mod_basic)
        self.assertEqual(
            data,
            Module(
                "test_mod_basic",
                "test_mod_basic",
                (
                    Class("myClass", (
                        Unknown('myMethod', 'Depth Exceeded: <function myClass.myMethod at memory_address>'),
                        Unknown('myStatic', 'Depth Exceeded: <function myClass.myStatic at memory_address>'),
                    )),
                    Func(
                        "myFunc",
                        (
                            Arg("a", UNKNOWN, POSITIONAL | KEYWORD),
                            Arg("b", UNKNOWN, POSITIONAL | KEYWORD),
                            Arg("c", UNKNOWN, KEYWORD | VARIADIC),
                        ),
                        UNKNOWN,
                    ),
                    Func(
                        "myLambda", (Arg("x", UNKNOWN, POSITIONAL | KEYWORD),), UNKNOWN
                    ),
                    Module("myModule", "test_mod_basic.myModule", (
                        Unknown('myVar', 'Depth Exceeded: [1, 2, 3]'),
                    )),
                    Var("myVar", "int"),
                ),
            ),
        )

    def test_all_filter(self):
        import test_all_filter

        data = Traversal(all_filter=True).traverse(test_all_filter)
        self.assertEqual(
            data,
            Module(
                "test_all_filter",
                "test_all_filter",
                (Func("A", (), UNKNOWN), Func("B", (), UNKNOWN)),
            ),
        )

    def test_exclude_modules(self):
        import test_exclude_modules

        data = Traversal(exclude_modules=True).traverse(test_exclude_modules)
        self.assertEqual(
            data,
            Module(
                "test_exclude_modules",
                "test_exclude_modules",
                (Module("af", "test_all_filter", ()), Func("func", (), UNKNOWN)),
            ),
        )

    def test_err_attr(self):
        import test_mod_errors.errMethod as errMethod

        data = Traversal().traverse(errMethod)
        self.assertEqual(
            data,
            Module(
                "errMethod",
                "test_mod_errors.errMethod",
                (
                    Class(
                        "Methods",
                        (
                            Unknown("err_method", "more like funtime error"),
                            Var("ok_method", "str"),
                        ),
                    ),
                ),
            ),
        )

    def test_err_attr(self):
        import test_mod_basic.cycleA as cycleA

        data = Traversal().traverse(cycleA)
        self.assertEqual(
            data,
            Module(
                "cycleA",
                "test_mod_basic.cycleA",
                (
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
                                                "Circular Reference: <class 'test_mod_basic.cycleA.CycleA'>",
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def test_stdlib(self):
        # Run through standard lib to see if anything breaks
        modules = sys.builtin_module_names
        for module in modules:
            data = list(get_api(module))
            self.assertTrue(len(data))


if __name__ == "__main__":
    unittest.main()
