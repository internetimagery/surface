""" Colllect typing info """

if False:  # type checking
    from typing import *


import re
import ast
import types
import token
import inspect
import tokenize
import itertools
import sigtools  # type: ignore

from surface._base import UNKNOWN
from surface._doc import parse_docstring

try:
    import typing
except ImportError:
    typing_attrs = (
        "AbstractSet",
        "AsyncIterable",
        "AsyncIterator",
        "Awaitable",
        "BinaryIO",
        "ByteString",
        "Callable",
        "Collection",
        "Container",
        "ContextManager",
        "Coroutine",
        "DefaultDict",
        "Dict",
        "FrozenSet",
        "Generator",
        "Generic",
        "IO",
        "ItemsView",
        "Iterable",
        "Iterator",
        "KeysView",
        "List",
        "Mapping",
        "MappingView",
        "MutableMapping",
        "MutableSequence",
        "MutableSet",
        "Reversible",
        "Sequence",
        "Set",
        "SupportsAbs",
        "SupportsBytes",
        "SupportsComplex",
        "SupportsFloat",
        "SupportsInt",
        "SupportsRound",
        "TextIO",
        "Tuple",
        "Type",
        "ValuesView",
        "_Protocol",
    )  # type: Tuple[str, ...]
else:
    typing_attrs = tuple(
        at for at in dir(typing) if isinstance(getattr(typing, at), typing.GenericMeta)
    )


__all__ = ["get_type", "get_type_func", "UNKNOWN"]

type_comment_reg = re.compile(r"# +type: ([\w ,\[\]\.]+)")
type_comment_sig_reg = re.compile(r"# +type: \(([\w ,\[\]\.]*)\) +-> +([\w ,\[\]\.]+)")
type_attr_reg = re.compile(r"(?:typing\.)?({})".format("|".join(typing_attrs)))


def get_type(value, name="", parent=None):  # type: (Any, str, Any) -> str
    return (
        get_comment_type(value, name, parent)
        or get_annotate_type(value, name, parent)
        or get_live_type(value)
    )


def get_type_func(
    value, name="", parent=None
):  # type: (Any, str, Any) -> Tuple[List[str], str]
    return (
        get_comment_type_func(value)
        or get_docstring_type_func(value)
        or get_annotate_type_func(value, name)
    )


def get_comment_type_func(value):  # type: (Any) -> Optional[Tuple[List[str], str]]
    try:
        source = inspect.getsource(value)
    except IOError:
        return None
    params = []
    sig_comment = None
    in_sig = False

    lines = iter(source.splitlines(True))
    readline = lambda: next(lines)
    tokenizer = tokenize.generate_tokens(readline)
    for tok in tokenizer:
        if not in_sig and tok[0] == token.NAME and tok[1] == "def":
            in_sig = True
        elif in_sig and tok[0] == token.NEWLINE:
            tok = next(tokenizer)
            sig_comment = sig_comment or type_comment_sig_reg.match(tok[1])
            break
        elif in_sig and tok[0] == tokenize.COMMENT:
            param = type_comment_reg.match(tok[1])
            if param:
                params.append(normalize(param.group(1).strip()))
            sig_comment = sig_comment or type_comment_sig_reg.match(tok[1])
    if not sig_comment:
        return None

    # Validate the same number of params as comment params? Assume mypy etc will do it for us?

    return_type = sig_comment.group(2)
    param_comment = sig_comment.group(1).strip()
    if param_comment and param_comment != "...":
        param_ast = ast.parse(param_comment).body[0].value  # type: ignore
        if isinstance(param_ast, ast.Tuple) and param_ast.elts:
            params = [
                normalize(
                    param_comment[
                        param_ast.elts[i].col_offset : param_ast.elts[i + 1].col_offset
                    ]
                )
                .rsplit(",", 1)[0]
                .strip()
                for i in range(len(param_ast.elts) - 1)
            ]
            params.append(
                normalize(param_comment[param_ast.elts[-1].col_offset :].strip())
            )
        else:
            params = [normalize(param_comment)]
    if return_type:
        return params, normalize(return_type)

    return None


def get_docstring_type_func(value):  # type: (Any) -> Optional[Tuple[List[str], str]]
    doc = inspect.getdoc(value)
    if not doc:
        return None
    result = parse_docstring(doc)
    if not result:
        return None
    params_dict, return_type = result
    if params_dict:
        sig = sigtools.signature(value)
        params = [params_dict.get(name, UNKNOWN) for name in sig.parameters]
    else:
        params = []
    return params, return_type


def get_annotate_type_func(value, name):  # type: (Any, str) -> Tuple[List[str], str]
    sig = sigtools.signature(value)
    return_type = (
        handle_live_annotation(sig.return_annotation)
        if sig.return_annotation is not sig.empty
        else UNKNOWN
    )
    if return_type == UNKNOWN and name == "__init__":
        return_type = "None"
    parameters = []
    for param in sig.parameters.values():
        if param.annotation is not sig.empty:
            # If we are given an annotation, use it
            parameters.append(handle_live_annotation(param.annotation))
        elif param.default is not sig.empty:
            # If we have a default value, use that type
            if param.default is None:
                # Value is optional
                parameters.append("typing.Optional[{}]".format(UNKNOWN))
            else:
                parameters.append(get_live_type(param.default))
        else:
            parameters.append(UNKNOWN)
    return parameters, return_type


def get_docstring_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    if inspect.isfunction(value):
        result = get_docstring_type_func(value)
        if result:
            params, return_type = result
            return "typing.Callable[{}, {}]".format(
                "[{}]".format(", ".join(normalize(p) for p in params))
                if params
                else "...",
                normalize(return_type),
            )
    return None


def get_comment_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    if inspect.isfunction(value):
        result = get_comment_type_func(value)
        if result:
            params, return_type = result
            return "typing.Callable[{}, {}]".format(
                "[{}]".format(", ".join(params)) if params else "...", return_type
            )
    return None


def get_annotate_type(value, name, parent):  # type: (Any, str, Any) -> Optional[str]
    if type(value) == types.FunctionType:
        params, return_type = get_annotate_type_func(value, name)
        return "typing.Callable[{}, {}]".format(
            "[{}]".format(", ".join(params)) if params else "...", return_type
        )
    elif inspect.isclass(parent) or inspect.ismodule(parent):
        annotation = getattr(parent, "__annotations__", {})
        if name in annotation:
            return handle_live_annotation(annotation[name])
    return None


def get_live_type(value):  # type: (Any) -> str
    # Standard types
    value_type = type(value)
    return (
        handle_live_standard_type(value_type)
        or handle_live_container_type(value, value_type)
        or handle_live_abstract(value, value_type)
        or UNKNOWN
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
        return "typing.List[{}]".format(get_live_type(value[0]) if value else UNKNOWN)
    if value_type == tuple:
        internals = [get_live_type(item) for item in value]
        if not internals:
            internals = ["{}, ...".format(UNKNOWN)]
        return "typing.Tuple[{}]".format(", ".join(internals))

    # Hashies!
    if value_type == set:
        template = "typing.Set[{}]"
        for item in value:
            return template.format(get_live_type(item))
        return template.format(UNKNOWN)
    if value_type == dict:
        template = "typing.Dict[{}, {}]"
        for k, v in value.items():
            return template.format(get_live_type(k), get_live_type(v))
        return template.format(UNKNOWN, UNKNOWN)

    # Generators
    # IMPORTANT!
    #     Taking an item out of the generator here to get the type is fine for cli usage.
    #     But if used during a live session this would be an problem.
    if value_type == types.GeneratorType:
        # NOTE: Generator return value can be taken from StopIteration return value if needed.
        template = "typing.Iterable[{}]"
        for item in value:
            return template.format(get_live_type(item))
        return template.format(UNKNOWN)
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
    if type(value) == types.FunctionType:
        return get_live_type(value)
    return UNKNOWN


# This is a bit of a brute force way of ensuring typing declarations are abspath.
# It does not take into account locally overidding names in typing module
# It is also not making arbitrary types absolute.
# Could be improved with a lot of static parsing, but for now this should be ok!
def normalize(type_string):  # type: (str) -> str
    return type_attr_reg.sub(r"typing.\1", type_string)
