import unittest
import types
import imp
import os.path

from surface._utils import clean_repr, abs_type


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


class TestNormalizeType(unittest.TestCase):
    def test_nothing(self):
        self.assertEqual("int", abs_type("int", {}))
        self.assertEqual("typing.List[str]", abs_type("List[str]", {}))
        self.assertEqual(
            "typing.Dict[typing.Tuple[int, str], typing.List[str]]",
            abs_type("Dict[Tuple[int, str], List[str]]", {}),
        )
        self.assertEqual("typing.Tuple[int, ...]", abs_type("Tuple[int, ...]", {}))

    def test_aliases(self):
        import datetime

        cxt = datetime.__dict__

        self.assertEqual("datetime.date", abs_type("date", cxt))
        self.assertEqual("typing.List[datetime.date]", abs_type("List[date]", cxt))
        self.assertEqual(
            "typing.Dict[typing.Tuple[int, ...], datetime.date]",
            abs_type("Dict[Tuple[int, ...], date]", cxt),
        )
        mod = imp.load_source(
            "mymodule",
            os.path.join(os.path.dirname(__file__), "testdata", "test_utils.py"),
        )
        cxt = mod.__dict__
        self.assertEqual("mymodule.List[int]", abs_type("List[int]", cxt))
        self.assertEqual("mymodule.List.method", abs_type("List.method", cxt))


if __name__ == "__main__":
    unittest.main()
