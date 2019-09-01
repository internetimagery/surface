import sys
import os.path
import unittest

from surface import get_api
from surface._traversal import Traversal, recurse, CircularWarn, DepthWarn
from surface._base import *
from surface._utils import clean_repr

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
            API.Module(
                "test_mod_basic",
                "test_mod_basic",
                (
                    API.Class(
                        "myClass",
                        "test_mod_basic.myClass",
                        (
                            API.Func(
                                "myMethod",
                                (
                                    API.Arg(
                                        "a", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD
                                    ),
                                    API.Arg(
                                        "b", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD
                                    ),
                                    API.Arg(
                                        "c",
                                        "int",
                                        Kind.POSITIONAL | Kind.KEYWORD | Kind.DEFAULT,
                                    ),
                                ),
                                UNKNOWN,
                            ),
                            API.Var("myProp", "int"),
                            API.Func(
                                "myStatic",
                                (
                                    API.Arg(
                                        "a", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD
                                    ),
                                    API.Arg(
                                        "b", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD
                                    ),
                                    API.Arg(
                                        "c", UNKNOWN, Kind.POSITIONAL | Kind.VARIADIC
                                    ),
                                ),
                                UNKNOWN,
                            ),
                            API.Var("myVar", "int"),
                        ),
                    ),
                    API.Func(
                        "myFunc",
                        (
                            API.Arg("a", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD),
                            API.Arg("b", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD),
                            API.Arg("c", UNKNOWN, Kind.KEYWORD | Kind.VARIADIC),
                        ),
                        UNKNOWN,
                    ),
                    API.Func(
                        "myLambda",
                        (API.Arg("x", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD),),
                        UNKNOWN,
                    ),
                    API.Module(
                        "myModule",
                        "test_mod_basic.myModule",
                        (
                            API.Class(
                                "MyEnumGroup",
                                "test_mod_basic.myModule.MyEnumGroup",
                                (
                                    API.Var("myEnumVar", "int"),
                                    API.Func(
                                        "__new__",
                                        (
                                            API.Arg(
                                                "value",
                                                UNKNOWN,
                                                Kind.POSITIONAL | Kind.KEYWORD,
                                            ),
                                        ),
                                        UNKNOWN,
                                    ),
                                    API.Func(
                                        "__call__",
                                        (
                                            API.Arg(
                                                "names",
                                                "typing.Union[NoneType, {}]".format(UNKNOWN),
                                                Kind.POSITIONAL
                                                | Kind.KEYWORD
                                                | Kind.DEFAULT,
                                            ),
                                            API.Arg(
                                                "module",
                                                "typing.Union[NoneType, {}]".format(UNKNOWN),
                                                Kind.POSITIONAL
                                                | Kind.KEYWORD
                                                | Kind.DEFAULT,
                                            ),
                                            API.Arg(
                                                "type",
                                                "typing.Union[NoneType, {}]".format(UNKNOWN),
                                                Kind.POSITIONAL
                                                | Kind.KEYWORD
                                                | Kind.DEFAULT,
                                            ),
                                            API.Arg(
                                                "start",
                                                "int",
                                                Kind.POSITIONAL
                                                | Kind.KEYWORD
                                                | Kind.DEFAULT,
                                            ),
                                        )
                                        if PY2
                                        else (
                                            API.Arg(
                                                "names",
                                                "typing.Union[NoneType, {}]".format(UNKNOWN),
                                                Kind.POSITIONAL
                                                | Kind.KEYWORD
                                                | Kind.DEFAULT,
                                            ),
                                            API.Arg(
                                                "module",
                                                "typing.Union[NoneType, {}]".format(UNKNOWN),
                                                Kind.KEYWORD | Kind.DEFAULT,
                                            ),
                                            API.Arg(
                                                "qualname",
                                                "typing.Union[NoneType, {}]".format(UNKNOWN),
                                                Kind.KEYWORD | Kind.DEFAULT,
                                            ),
                                            API.Arg(
                                                "type",
                                                "typing.Union[NoneType, {}]".format(UNKNOWN),
                                                Kind.KEYWORD | Kind.DEFAULT,
                                            ),
                                            API.Arg(
                                                "start",
                                                "int",
                                                Kind.KEYWORD | Kind.DEFAULT,
                                            ),
                                        ),
                                        UNKNOWN,
                                    ),
                                ),
                            ),
                            API.Var("myVar", "typing.List[int]"),
                        ),
                    ),
                    API.Var("myVar", "int"),
                ),
            ),
        )

    def test_depth(self):
        import test_mod_basic

        data = Traversal(depth=1).traverse(test_mod_basic)
        self.assertEqual(
            data,
            API.Module(
                "test_mod_basic",
                "test_mod_basic",
                (
                    API.Class(
                        "myClass",
                        "test_mod_basic.myClass",
                        (
                            API.Unknown(
                                "myMethod",
                                DepthWarn,
                                clean_repr(repr(test_mod_basic.myClass.myMethod)),
                            ),
                            API.Unknown(
                                "myProp",
                                DepthWarn,
                                clean_repr(repr(test_mod_basic.myClass.myProp)),
                            ),
                            API.Unknown(
                                "myStatic",
                                DepthWarn,
                                clean_repr(repr(test_mod_basic.myClass.myStatic)),
                            ),
                            API.Unknown(
                                "myVar",
                                DepthWarn,
                                clean_repr(repr(test_mod_basic.myClass.myVar)),
                            ),
                        ),
                    ),
                    API.Func(
                        "myFunc",
                        (
                            API.Arg("a", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD),
                            API.Arg("b", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD),
                            API.Arg("c", UNKNOWN, Kind.KEYWORD | Kind.VARIADIC),
                        ),
                        UNKNOWN,
                    ),
                    API.Func(
                        "myLambda",
                        (API.Arg("x", UNKNOWN, Kind.POSITIONAL | Kind.KEYWORD),),
                        UNKNOWN,
                    ),
                    API.Module(
                        "myModule",
                        "test_mod_basic.myModule",
                        (
                            API.Unknown(
                                "MyEnumGroup",
                                DepthWarn,
                                clean_repr(repr(test_mod_basic.myModule.MyEnumGroup)),
                            ),
                            API.Unknown(
                                "myVar",
                                DepthWarn,
                                clean_repr(repr(test_mod_basic.myModule.myVar)),
                            ),
                        ),
                    ),
                    API.Var("myVar", "int"),
                ),
            ),
        )

    def test_all_filter(self):
        import test_all_filter

        data = Traversal(all_filter=True).traverse(test_all_filter)
        self.assertEqual(
            data,
            API.Module(
                "test_all_filter",
                "test_all_filter",
                (API.Func("A", (), UNKNOWN), API.Func("B", (), UNKNOWN)),
            ),
        )

    def test_exclude_modules(self):
        import test_exclude_modules

        data = Traversal(exclude_modules=True).traverse(test_exclude_modules)
        self.assertEqual(
            data,
            API.Module(
                "test_exclude_modules",
                "test_exclude_modules",
                (
                    API.Module("af", "test_all_filter", ()),
                    API.Func("func", (), UNKNOWN),
                ),
            ),
        )

    def test_err_attr(self):
        import test_mod_errors.errMethod as errMethod

        data = Traversal().traverse(errMethod)
        self.assertEqual(
            data,
            API.Module(
                "errMethod",
                "test_mod_errors.errMethod",
                (
                    API.Class(
                        "Methods",
                        (
                            API.Unknown(
                                "err_method", "RuntimeError", "more like funtime error"
                            ),
                            API.Var("ok_method", "str"),
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
            API.Module(
                "cycleA",
                "test_mod_basic.cycleA",
                (
                    API.Class(
                        "CycleA",
                        "test_mod_basic.cycleA.CycleA",
                        (
                            API.Class(
                                "cycle",
                                "test_mod_basic.cycleB.CycleB",
                                (
                                    API.Class(
                                        "cycle",
                                        "test_mod_basic.cycleA.CycleA",
                                        (
                                            API.Unknown(
                                                "cycle",
                                                CircularWarn,
                                                "<class 'test_mod_basic.cycleA.CycleA'>",
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
