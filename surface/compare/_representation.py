

class BaseRepresentation(object):

    def __init__(self, wrapped):
        pass


class Reference(BaseRepresentation):
    """ Refer to an object from another module. Eg an import / assignment """
    pass


class Class(BaseRepresentation):
    """ Class! """
    pass
# TODO: may need to walk "bases" tree to get inherited methods
# TODO: can't find parent? Can't check methods, that is ok!


class Function(BaseRepresentation):
    """ Function! Also includes methods / staticmethods etc """
    pass

class Attribute(BaseRepresentation):
    """ Pretty much anything else! """
    pass