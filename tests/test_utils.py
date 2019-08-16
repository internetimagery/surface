import unittest
import types
import imp
import os.path

from surface._utils import clean_repr, normalize_type


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
        self.assertEqual("int", normalize_type("int", "", [], "", []))
        self.assertEqual("typing.List[str]", normalize_type("List[str]", "", [], "", []))
        self.assertEqual(
            "typing.Dict[typing.Tuple[int, str], typing.List[str]]",
            normalize_type("Dict[Tuple[int, str], List[str]]", "", [], "", []),
        )
        self.assertEqual(
            "typing.Tuple[int, ...]", normalize_type("Tuple[int, ...]", "", [], "", [])
        )

    def test_aliases(self):
        import datetime
        name = "datetime"
        cxt = list(datetime.__dict__)

        self.assertEqual("datetime.date", normalize_type("date", "", [], name, cxt))
        self.assertEqual(
            "typing.List[datetime.date]",
            normalize_type("List[date]", "", [], name, cxt),
        )
        self.assertEqual(
            "typing.Dict[typing.Tuple[int, ...], datetime.date]",
            normalize_type("Dict[Tuple[int, ...], date]", "", [], name, cxt),
        )
        mod = imp.load_source(
            "mymodule",
            os.path.join(os.path.dirname(__file__), "testdata", "test_utils.py"),
        )
        name = "mymodule"
        cxt = mod.__dict__
        self.assertEqual(
            "mymodule.List[int]", normalize_type("List[int]", "", [], name, cxt)
        )
        self.assertEqual(
            "mymodule.List.method", normalize_type("List.method", "", [], name, cxt)
        )


if __name__ == "__main__":
    unittest.main()
