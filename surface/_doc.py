""" Parse typing information out of docstrings """

if False:  # type checking
    from typing import *

import re
import inspect

from surface._base import UNKNOWN, TYPE_CHARS
from surface._utils import normalize_type


def parse_docstring(func):  # type: (Any) -> Optional[Tuple[Dict[str, str], str]]
    """ Parse out typing information from docstring """
    if not inspect.isfunction(func) and not inspect.ismethod(func):
        # Classes should be handled, but are not yet...
        # Handling them would involve determining if they use __new__ or __init__
        # and using that as the function itself.
        return None

    doc = inspect.getdoc(func)
    if not doc:
        return None
    context = func.__globals__
    return handle_google(doc, context)


def handle_google(
    docstring, context
):  # type: (str, Dict[str, Any]) -> Optional[Tuple[Dict[str, str], str]]
    # Find the first header, to establish indent
    header = re.search(r"^([ \t]*)[a-zA-Z]+:\s*$", docstring, re.M)
    if not header:
        return None
    params = {}  # type: Dict[str, str]
    return_type = None
    header_indent = header.group(1)
    headers = [
        m
        for m in re.finditer(
            r"^{}([a-zA-Z]+):\s*$".format(header_indent), docstring, re.M
        )
    ]
    for i, header in enumerate(headers):
        header_name = header.group(1).lower()
        if header_name in ("arg", "args", "arguments", "parameters"):
            params = {
                p.group(1): normalize_type(p.group(2), context)
                for p in re.finditer(
                    r"^{}[ \t]+([\w\-]+) *\(`?({})`?\)(?: *: .+| *)$".format(
                        header_indent, TYPE_CHARS
                    ),
                    docstring[
                        header.end() : headers[i + 1].start()
                        if i < len(headers) - 1
                        else len(docstring)
                    ],
                    re.M,
                )
            }
        elif header_name in ("yield", "yields", "return", "returns"):
            returns = re.search(
                r"^{}[ \t]+(`?{}`?)(?: *: .+| *)$".format(header_indent, TYPE_CHARS),
                docstring[header.end() :],
                re.M,
            )
            if returns:
                return_type = normalize_type(returns.group(1), context)
                if "yield" in header_name:
                    return_type = "typing.Iterable[{}]".format(return_type)
    if params or return_type:
        return params, return_type or UNKNOWN
    return None
