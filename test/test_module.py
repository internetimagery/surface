import shutil
import os.path
import unittest
import tempfile

from surface._module import map_modules


class TestModule(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    @staticmethod
    def make_file(name, root):
        with open(os.path.join(root, "{}.py".format(name)), "w"):
            pass

    def make_module(self, name, root):
        os.mkdir(os.path.join(root, name))
        self.make_file("__init__", os.path.join(root, name))

    def test_single(self):
        self.make_file("testing123", self.root)
        filepath = os.path.join(self.root, "testing123.py")
        self.assertEqual(map_modules([filepath]), {"testing123": filepath})

    def test_module(self):
        self.make_module("testing123", self.root)
        filepath = os.path.join(self.root, "testing123", "__init__.py")
        self.assertEqual(map_modules([filepath]), {"testing123": filepath})

    def test_submodules(self):
        self.make_module("testing123", self.root)
        root = os.path.join(self.root, "testing123")
        self.make_file("testing456", root)
        self.make_module("testing789", root)
        self.assertEqual(
            map_modules([self.root]),
            {
                "testing123": os.path.join(root, "__init__.py"),
                "testing123.testing456": os.path.join(root, "testing456.py"),
                "testing123.testing789": os.path.join(
                    root, "testing789", "__init__.py"
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()
