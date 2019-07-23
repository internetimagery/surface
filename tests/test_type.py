import unittest

from surface._type import get_live_type


class TestLiveType(unittest.TestCase):
    def test_standard(self):
        self.assertEqual("int", get_live_type(123))
        self.assertEqual("float", get_live_type(123.00))
        self.assertEqual("complex", get_live_type(2 + 3j))
        self.assertEqual("str", get_live_type("abc"))
        self.assertEqual("bool", get_live_type(True))
        try:
            self.assertEqual("unicode", get_live_type(unicode("abc")))
        except NameError:  # python 2
            pass

    def test_collections(self):
        self.assertEqual("typing.List[typing.Any]", get_live_type([]))
        self.assertEqual("typing.List[int]", get_live_type([123, 456]))
        self.assertEqual("typing.Set[typing.Any]", get_live_type(set()))
        self.assertEqual("typing.Set[int]", get_live_type(set([123, 456])))
        self.assertEqual("typing.Tuple[typing.Any, ...]", get_live_type(tuple()))
        self.assertEqual("typing.Tuple[int, str]", get_live_type(tuple([123, "456"])))
        self.assertEqual("typing.Dict[typing.Any, typing.Any]", get_live_type({}))
        self.assertEqual("typing.Dict[int, str]", get_live_type({123: "456"}))


if __name__ == "__main__":
    unittest.main()
