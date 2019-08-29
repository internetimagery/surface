import unittest
import types
import imp
import os.path

from surface._utils import clean_repr


class A(object):
    def err(self):
        raise RuntimeError("Error {}".format(self))


class TestCleanRepr(unittest.TestCase):
    def test_exception_clean(self):
        a1, a2 = A(), A()
        try:
            a1.err()
        except RuntimeError as err:
            err1 = str(err)
        try:
            a2.err()
        except RuntimeError as err:
            err2 = str(err)
        clean1, clean2 = clean_repr(err1), clean_repr(err2)
        self.assertNotEqual(err1, err2)
        self.assertEqual(clean1, clean2)


if __name__ == "__main__":
    unittest.main()
