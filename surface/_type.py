""" Colllect typing info """

if False:  # type checking
    from typing import Any, Tuple, List, Optional

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
    # Standard types
    value_type = type(value)
    return (
        handle_standard_type(value_type)
        or handle_container_type(value, value_type)
        or "typing.Any"
    )


def handle_standard_type(value_type):  # type: (Any) -> Optional[str]
    # Numeric
    if value_type == int:
        return "int"
    if value_type == float:
        return "float"
    if value_type == complex:
        return "complex"

    # Strings
    if value_type == str:
        return "str"
    try: # python 2
        if value_type == unicode:  # type: ignore
            return "unicode"
    except NameError:
        pass

    # Aaaaaand the rest
    if value_type == bool:
        return "bool"

    return None


def handle_container_type(value, value_type):  # type: (Any, Any) -> Optional[str]
    # Sequences
    if value_type == list:
        return "typing.List[{}]".format(
            get_live_type(value[0]) if value else "typing.Any"
        )
    if value_type == tuple:
        internals = [get_live_type(item) for item in value]
        if not internals:
            internals = ["typing.Any, ..."]
        return "typing.Tuple[{}]".format(", ".join(internals))

    # Hashies!
    if value_type == set:
        template = "typing.Set[{}]"
        for item in value:
            return template.format(get_live_type(item))
        return template.format("typing.Any")
    if value_type == dict:
        template = "typing.Dict[{}, {}]"
        for k, v in value.items():
            return template.format(get_live_type(k), get_live_type(v))
        return template.format("typing.Any", "typing.Any")

    return None
