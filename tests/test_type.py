import sys
import os.path
import unittest

from surface._base import PY2
from surface._type import LiveType, FuncType, AnnotationType

path = os.path.join(os.path.dirname(__file__), "testdata")
if path not in sys.path:
    sys.path.insert(0, path)


class TestLiveType(unittest.TestCase):
    def test_standard(self):
        self.assertEqual("int", str(LiveType(123)))
        self.assertEqual("float", str(LiveType(123.00)))
        self.assertEqual("complex", str(LiveType(2 + 3j)))
        self.assertEqual("str", str(LiveType("abc")))
        self.assertEqual("bool", str(LiveType(True)))
        self.assertEqual("None", str(LiveType(None)))
        if PY2:
            self.assertEqual("unicode", str(LiveType(unicode("abc"))))

    def test_collections(self):
        self.assertEqual("typing.List[~unknown]", str(LiveType([])))
        self.assertEqual("typing.List[int]", str(LiveType([123, 456])))
        self.assertEqual("typing.Set[~unknown]", str(LiveType(set())))
        self.assertEqual("typing.Set[int]", str(LiveType(set([123, 456]))))
        self.assertEqual("typing.Tuple[~unknown, ...]", str(LiveType(tuple())))
        self.assertEqual("typing.Tuple[int, str]", str(LiveType(tuple([123, "456"]))))
        self.assertEqual("typing.Dict[~unknown, ~unknown]", str(LiveType({})))
        self.assertEqual("typing.Dict[int, str]", str(LiveType({123: "456"})))
        self.assertEqual("typing.Iterable[int]", str(LiveType((a for a in range(5)))))

    def test_abstract(self):
        self.assertEqual(
            "typing.Callable[[~unknown], ~unknown]", str(LiveType(lambda x: 123))
        )

        def test(a, b=None):
            pass

        self.assertEqual(
            "typing.Callable[[~unknown, typing.Optional[~unknown]], ~unknown]",
            str(LiveType(test)),
        )


@unittest.skipIf(PY2, "annotations not available")
class TestAnnotations(unittest.TestCase):
    def test_function(self):
        import test_annotation

        self.assertEqual(
            FuncType(test_annotation.func1).as_var(),
            "typing.Callable[[int, str], bool]",
        )
        self.assertEqual(
            FuncType(test_annotation.func2).as_var(),
            "typing.Callable[[typing.Callable[[int, str], bool], typing.List[str]], typing.List[bool]]",
        )
        self.assertEqual(
            FuncType(test_annotation.func3).as_var(),
            "typing.Callable[[test_annotation.Obj1], bool]",
        )
        self.assertEqual(
            FuncType(test_annotation.func4).as_var(),
            "typing.Callable[[int, str], bool]",
        )

        self.assertEqual(
            str(
                AnnotationType(
                    test_annotation.Obj1.__annotations__["attr1"],
                    test_annotation.__dict__,
                )
            ),
            "typing.List[int]",
        )
        self.assertEqual(
            str(
                AnnotationType(
                    test_annotation.__annotations__["variable1"],
                    test_annotation.__dict__,
                )
            ),
            "typing.List[str]",
        )


class TestComments(unittest.TestCase):
    def test_function(self):
        import test_comments

        self.assertEqual(
            FuncType(test_comments.func1).as_var(),
            "typing.Callable[[int, str, typing.Dict[str, typing.List[str]]], None]",
        )
        self.assertEqual(
            FuncType(test_comments.func2).as_var(), "typing.Callable[..., None]"
        )
        self.assertEqual(
            FuncType(test_comments.func3).as_var(),
            "typing.Callable[[int, typing.List[str], typing.Dict[str, typing.List[str]]], None]",
        )
        self.assertEqual(
            FuncType(test_comments.func4).as_var(),
            "typing.Callable[..., ~unknown]",
        )


class TestDocstring(unittest.TestCase):
    def test_function(self):
        import test_docstring

        self.assertEqual(
            FuncType(test_docstring.func1).as_var(),
            "typing.Callable[[int, str, typing.Dict[str, bool]], None]",
        )
        self.assertEqual(
            FuncType(test_docstring.func2).as_var(),
            "typing.Callable[[str], typing.Iterable[str]]",
        )
        self.assertEqual(
            FuncType(test_docstring.func3).as_var(), "typing.Callable[..., int]"
        )
        self.assertEqual(
            FuncType(test_docstring.func4).as_var(), "typing.Callable[[int], ~unknown]"
        )


if __name__ == "__main__":
    unittest.main()
