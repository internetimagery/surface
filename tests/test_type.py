import sys
import os.path
import unittest

from surface._type import (
    get_live_type,
    get_annotate_type,
    get_comment_type,
    get_docstring_type,
)

path = os.path.join(os.path.dirname(__file__), "testdata")
if path not in sys.path:
    sys.path.insert(0, path)


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
        self.assertEqual("typing.List[~unknown]", get_live_type([]))
        self.assertEqual("typing.List[int]", get_live_type([123, 456]))
        self.assertEqual("typing.Set[~unknown]", get_live_type(set()))
        self.assertEqual("typing.Set[int]", get_live_type(set([123, 456])))
        self.assertEqual("typing.Tuple[~unknown, ...]", get_live_type(tuple()))
        self.assertEqual("typing.Tuple[int, str]", get_live_type(tuple([123, "456"])))
        self.assertEqual("typing.Dict[~unknown, ~unknown]", get_live_type({}))
        self.assertEqual("typing.Dict[int, str]", get_live_type({123: "456"}))
        self.assertEqual("typing.Iterable[int]", get_live_type((a for a in range(5))))

    def test_abstract(self):
        self.assertEqual(
            "typing.Callable[[~unknown], ~unknown]", get_live_type(lambda x: 123)
        )

        def test(a, b=None):
            pass

        self.assertEqual(
            "typing.Callable[[~unknown, typing.Optional[~unknown]], ~unknown]",
            get_live_type(test),
        )


@unittest.skipIf(sys.version_info.major < 3, "annotations not available")
class TestAnnotations(unittest.TestCase):
    def test_function(self):
        import test_annotation

        self.assertEqual(
            get_annotate_type(test_annotation.func1, "func1", test_annotation),
            "typing.Callable[[int, str], bool]",
        )
        self.assertEqual(
            get_annotate_type(test_annotation.func2, "func2", test_annotation),
            "typing.Callable[[typing.Callable[[int, str], bool], typing.List[str]], typing.List[bool]]",
        )
        self.assertEqual(
            get_annotate_type(test_annotation.func3, "func3", test_annotation),
            "typing.Callable[[test_annotation.Obj1], bool]",
        )
        self.assertEqual(
            get_annotate_type(
                test_annotation.Obj1.attr1, "attr1", test_annotation.Obj1
            ),
            "typing.List[int]",
        )
        self.assertEqual(
            get_annotate_type(test_annotation.variable1, "variable1", test_annotation),
            "typing.List[str]",
        )


class TestComments(unittest.TestCase):
    def test_function(self):
        import test_comments

        self.assertEqual(
            get_comment_type(test_comments.func1, "func1", test_comments),
            "typing.Callable[[int, str, Dict[str, List[str]]], None]",
        )
        self.assertEqual(
            get_comment_type(test_comments.func2, "func2", test_comments),
            "typing.Callable[..., None]",
        )
        self.assertEqual(
            get_comment_type(test_comments.func3, "func3", test_comments),
            "typing.Callable[[int, List[str], Dict[str, List[str]]], None]",
        )


class TestDocstring(unittest.TestCase):
    def test_function(self):
        import test_docstring

        self.assertEqual(
            get_docstring_type(test_docstring.func1, "func1", test_docstring),
            "typing.Callable[[int, str, Dict[str, bool]], None]",
        )
        self.assertEqual(
            get_docstring_type(test_docstring.func2, "func2", test_docstring),
            "typing.Callable[[str], typing.Iterable[str]]",
        )


if __name__ == "__main__":
    unittest.main()
