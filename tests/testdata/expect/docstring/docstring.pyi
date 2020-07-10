# Automatically generated stub file; Generated by 'surface' (pip install surface).
# Module: docstring

import typing
import typing.re

class ClassDoc(object):
    """
        Typing information in docstring
        Args:
            name (str)
    """

    def __init__(self, name: str) -> None:
        ""

class RegularDoc(object):
    ""

    def __init__(self, name: str, index: int) -> None:
        """
            Some information
            Args:
                name (str):
                index (int):
        """

    @classmethod
    def class_doc(cls, regex: typing.re.Pattern) -> bool:
        """
            some value becomes another
            Params:
                regex (Pattern)
            Returns:
                bool
        """

    def method_doc(self, classdoc: ClassDoc) -> typing.Any:
        """
            Some method
            Args:
                classdoc (:class:`ClassDoc`): the class doc!
        """

    @staticmethod
    def static_doc(input_: typing.Optional[str] = ...) -> int:
        """
            Give me an input!
            Args:
                input_ (Optional[str]): some string, maybe
            Returns:
                int: some number
        """

def function_doc(day: int, month: int, year: int) -> typing.Iterator[int]:
    """
        Is it the second?
        Arguments:
            day (int): day of the month (01)
            month (int): month of the year (02)
            year (int): Year! four digits! (1999)
        Yields:
            int: days!
    """