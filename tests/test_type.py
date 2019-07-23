import unittest

from surface._type import get_live_type


class TestLiveType(unittest.TestCase):
    def test_standard(self):
        self.assertEqual("int", get_live_type(123))
        self.assertEqual("float", get_live_type(123.00))
        self.assertEqual("complex", get_live_type(2 + 3j))
        self.assertEqual("str", get_live_type("abc"))
        self.assertEqual("bool", get_live_type(True))
        self.assertEqual("None", get_live_type(None))
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
        self.assertEqual("typing.Iterable[int]", get_live_type((a for a in range(5))))

    def test_abstract(self):
        self.assertEqual(
            "typing.Callable[[typing.Any], typing.Any]", get_live_type(lambda x: 123)
        )

        def test(a, b=None):
            pass

        self.assertEqual(
            "typing.Callable[[typing.Any, typing.Optional[typing.Any]], typing.Any]",
            get_live_type(test),
        )
        try:
            import typing
            from surface._base import Func

            exec(
                "def test2(a: int, b: typing.List[int]) -> int: pass",
                locals(),
                globals(),
            )
            exec("def test3(a: Func, b=None) -> int: pass", locals(), globals())
        except (ImportError, SyntaxError):
            pass  # Python 2
        else:
            self.assertEqual(
                "typing.Callable[[int, typing.List[int]], int]", get_live_type(test2)
            )  # type: ignore
            self.assertEqual(
                "typing.Callable[[surface._base.Func, typing.Optional[typing.Any]], int]",
                get_live_type(test3),
            )  # type: ignore


if __name__ == "__main__":
    unittest.main()
