

class ClassDoc(object):
    """ Typing information in docstring
        Args:
            name (str)
    """

    def __init__(self, name):
        ""
        self._name = name


class RegularDoc(object):

    def __init__(self, name, index):
        """ 
        Some information
        Args:
            name (str):
            index (int):
        """
        self._name = name
        self._index = index

    @classmethod
    def class_doc(cls, regex):
        """

        some value becomes another
        Params:
            regex (Pattern)
        Returns:
            bool
        """
        return bool(regex.match("hello"))
    
    def method_doc(self, classdoc):
        """ Some method
        Args:
            classdoc (:class:`ClassDoc`): the class doc!
        """
        print("CLASSDOC", classdoc)
    
    @staticmethod
    def static_doc(input_=None):
        """ Give me an input!
        Args:
            input_ (Optional[Dict[str, List[int]]]): some string, maybe
        Returns:
            int: some number
        """
        if input_ is None:
            print("Oh no!")
        return 0
    
def function_doc(day, month, year):
    """ Is it the second?
        Arguments:
            day (int): day of the month (01)
            month (int): month of the year (02)
            year (int): Year! four digits! (1999)
        Yields:
            int: days!
    """
    for i in range(day):
        if i % 2:
            yield i

def function_bad_doc(value):
    """ Not a valid docstring
        Args:
            not an argument
        Returns:
            something not a type
    """
    print("BAH!")