class MyType(object):
    pass


class OtherType(object):
    pass


def expose_type():  #  type: () -> OtherType
    return OtherType()
