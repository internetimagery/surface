import unittest

from surface._base import *
from surface._compare import *


class TestCompare(unittest.TestCase):
    def test_nothing(self):
        api_old = api_new = {"my_api": [Var("stuff", "float")]}
        changes = compare(api_old, api_new)
        self.assertEqual(changes, set())

    def test_patch(self):
        api_old = {
            "my_api": [
                Func(
                    "thing",
                    [
                        Arg("first", "int", POSITIONAL),
                        Arg("args", "int", POSITIONAL | VARIADIC),
                    ],
                    "int",
                )
            ]
        }
        api_new = {
            "my_api": [
                Func(
                    "thing",
                    [
                        Arg("second", "int", POSITIONAL),
                        Arg("rawr_args", "int", POSITIONAL | VARIADIC),
                    ],
                    "int",
                )
            ]
        }
        changes = compare(api_old, api_new)
        self.assertEqual(
            changes,
            set(
                [
                    Change(PATCH, "Renamed Arg: my_api.thing.(rawr_args)"),
                    Change(PATCH, "Renamed Arg: my_api.thing.(second)"),
                ]
            ),
        )

    def test_minor(self):
        pass  # TODO: !!

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
                    Change(MINOR, "Added: mymodule2"),
                    Change(MAJOR, "Removed: mymodule"),
                    Change(MAJOR, "Type Changed: othermodule.something"),
                    Change(MAJOR, "Type Changed: othermodule.somethingelse"),
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
