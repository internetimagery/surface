import imp
import os.path
import unittest

from surface._base import *
from surface._compare import *
from surface._traversal import APITraversal

root = os.path.join(os.path.dirname(__file__), "testdata", "test_mod_compare")


class TestCompare(unittest.TestCase):
    @staticmethod
    def get_module(name, rename=""):
        module = imp.load_source(
            rename or name, os.path.join(root, "{}.py".format(name))
        )
        api = {rename or name: list(APITraversal().traverse(module))}
        return api

    def test_no_change(self):
        patchA = self.get_module("patchA")
        changes = compare(patchA, patchA)
        self.assertEqual(changes, set())

    def test_patch(self):
        patchA = self.get_module("patchA")
        patchB = self.get_module("patchB", "patchA")
        changes = compare(patchA, patchB)
        self.assertEqual(
            changes,
            set(
                [
                    Change(
                        PATCH,
                        "Type Changed",
                        'patchA.func1.(b), Was: "~unknown", Now: "int"',
                    ),
                    Change(
                        PATCH,
                        "Return Type Changed",
                        'patchA.func1, Was: "~unknown", Now: "int"',
                    ),
                ]
            ),
        )

    def test_minor(self):
        minorA = self.get_module("minorA")
        minorB = self.get_module("minorB", "minorA")
        changes = compare(minorA, minorB)
        self.assertEqual(
            changes,
            set(
                [
                    Change("minor", "Added", "minorA.NewClass"),
                    Change("minor", "Added Arg", "minorA.func3.(args)"),
                    Change(
                        "minor", "Could not verify", "minorA.Failer.ohno: CANT GET THIS"
                    ),
                    Change("minor", "Added", "minorA.var2"),
                    Change("minor", "Added Arg", "minorA.func1.(b)"),
                    Change("minor", "Added", "minorA.Failer.new_attr"),
                    Change(
                        "minor",
                        "Return Type Changed",
                        'minorA.func2, Was: "typing.Dict[str, str]", Now: "typing.Mapping[str, str]"',
                    ),
                    Change(
                        "minor",
                        "Type Changed",
                        'minorA.func2.(a), Was: "typing.List[str]", Now: "typing.Sequence[str]"',
                    ),
                ]
            ),
        )

    def test_major(self):
        pass  # TODO: !1

    def test_basic(self):
        api_old = {
            "mymodule": [Var("something", "type")],
            "othermodule": [Var("something", "type"), Var("somethingelse", "int")],
        }
        api_new = {
            "mymodule2": [Var("something", "type")],
            "othermodule": [Func("something", [], "type"), Var("somethingelse", "str")],
        }
        changes = compare(api_old, api_new)
        self.assertEqual(
            changes,
            set(
                [
                    Change(MINOR, "Added", "mymodule2"),
                    Change(MAJOR, "Removed", "mymodule"),
                    Change(
                        MAJOR,
                        "Type Changed",
                        'othermodule.somethingelse, Was: "int", Now: "str"',
                    ),
                    Change(
                        MAJOR,
                        "Type Changed",
                        '''othermodule.something, Was: "<class 'surface._base.Var'>", Now: "<class 'surface._base.Func'>"''',
                    ),
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
