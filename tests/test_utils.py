import unittest

from surface._utils import clean_err


class A(object):
    def err(self):
        raise RuntimeError("Error {}".format(self))


class TestErrClean(unittest.TestCase):
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
        clean1, clean2 = clean_err(err1), clean_err(err2)
        self.assertNotEqual(err1, err2)
        self.assertEqual(clean1, clean2)


if __name__ == "__main__":
    unittest.main()
