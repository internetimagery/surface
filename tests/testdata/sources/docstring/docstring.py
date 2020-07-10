

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