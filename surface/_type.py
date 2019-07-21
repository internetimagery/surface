""" Colllect typing info """

__all__ = ["get_type"]


def get_type(value):  # type: (Any) -> str
    return get_comment_type(value) or get_annotate_type(value) or get_live_type(value)


def get_type_func(value):  # type: (Any) -> Tuple[List[str], str]
    # TODO: Get function typing
    pass


def get_comment_type(value):  # type: (Any) -> Optional[str]
    pass


def get_annotate_type(value):  # type: (Any) -> Optional[str]
    pass


def get_live_type(value):  # type: (Any) -> str
    # TODO: Get type from live value
    return "typing.Any"
