import unittest

from surface._base import *
from surface._compare import *


class TestCompare(unittest.TestCase):
    def test_basic(self):
        api_old = {
            "mymodule": [Var("something", "type")],
            "othermodule": [Var("something", "type")],
        }
        api_new = {
            "mymodule2": [Var("something", "type")],
            "othermodule": [Func("something", [], "type")],
        }
        changes = compare(api_old, api_new)
        self.assertEqual(
            changes,
            set(
                [
                    Change(MINOR, "Added: mymodule2"),
                    Change(MAJOR, "Removed: mymodule"),
                    Change(MAJOR, "Type Changed: othermodule.something"),
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
