""" Colllect typing info """

import types
import inspect
import sigtools  # type: ignore

if False:  # type checking
    from typing import Any, Tuple, List, Optional

__all__ = ["get_type", "get_type_func"]


def get_type(value):  # type: (Any) -> str
    return get_comment_type(value) or get_annotate_type(value) or get_live_type(value)


def get_type_func(value):  # type: (Any) -> Tuple[List[str], str]
    # TODO: Handle comment annotations as well
    sig = sigtools.signature(value)
    return_type = (
        handle_live_annotation(sig.return_annotation)
        if sig.return_annotation is not sig.empty
        else "typing.Any"
    )
    parameters = []
    for param in sig.parameters.values():
        if param.annotation is not sig.empty:
            # If we are given an annotation, use it
            parameters.append(handle_live_annotation(param.annotation))
        elif param.default is not sig.empty:
            # If we have a default value, use that type
            if param.default is None:
                # Value is optional
                parameters.append("typing.Optional[typing.Any]")
            else:
                parameters.append(get_live_type(param.default))
        else:
            parameters.append("typing.Any")
    return parameters, return_type


def get_comment_type(value):  # type: (Any) -> Optional[str]
    pass


def get_annotate_type(value):  # type: (Any) -> Optional[str]
    pass


def get_live_type(value):  # type: (Any) -> str
    # Standard types
    value_type = type(value)
    return (
        handle_live_standard_type(value_type)
        or handle_live_container_type(value, value_type)
        or handle_live_abstract(value, value_type)
        or "typing.Any"
    )


def handle_live_standard_type(value_type):  # type: (Any) -> Optional[str]
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
    try:  # python 2
        if value_type == unicode:  # type: ignore
            return "unicode"
    except NameError:
        pass

    # Aaaaaand the rest
    if value_type == bool:
        return "bool"
    if value_type == type(None):
        return "None"

    return None


def handle_live_container_type(value, value_type):  # type: (Any, Any) -> Optional[str]
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

    # Generators
    # IMPORTANT!
    #     Taking an item out of the generator here to get the type is fine for cli usage.
    #     But if used during a live session this would be an problem.
    if value_type == types.GeneratorType:
        # NOTE: Generator return value can be taken from StopIteration return value if needed.
        template = "typing.Iterable[{}]"
        for item in value:
            return template.format(get_live_type(item))
        return template.format("typing.Any")
    # TODO: handle types.AsyncGeneratorType

    return None


def handle_live_abstract(value, value_type):  # type: (Any, Any) -> Optional[str]
    if value_type == types.FunctionType:
        params, return_type = get_type_func(value)
        return "typing.Callable[{}, {}]".format(
            "[{}]".format(", ".join(params)) if params else "...", return_type
        )

    return None


# Python3 function
def handle_live_annotation(value):  # type: (Any) -> str
    import typing

    if type(value) == typing.GenericMeta:
        return str(value)
    if inspect.isclass(value):
        if value.__module__ == "builtins":
            return value.__name__
        return "{}.{}".format(value.__module__, value.__name__)
    return "typing.Any"
