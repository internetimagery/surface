""" Parse typing information out of docstrings """

if False:  # type checking
    from typing import *

import re
from surface._base import UNKNOWN

type_chars = r"[\w\-\[\]\., `]+"


def parse_docstring(docstring):  # type: (str) -> Optional[Tuple[Dict[str, str], str]]
    """ Parse out typing information from docstring """
    return handle_google(docstring)


def clean_type(type_str):  # type: (str) -> str
    return type_str.replace("`", "").strip()


def handle_google(docstring):  # type: (str) -> Optional[Tuple[Dict[str, str], str]]
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
                p.group(1): clean_type(p.group(2))
                for p in re.finditer(
                    r"^{}[ \t]+([\w\-]+) *\(({})\)(?: *: .+| *)$".format(
                        header_indent, type_chars
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
                r"^{}[ \t]+({})(?: *: .+| *)$".format(header_indent, type_chars),
                docstring[header.end() :],
                re.M,
            )
            if returns:
                return_type = clean_type(returns.group(1))
                if "yield" in header_name:
                    return_type = "typing.Iterable[{}]".format(return_type)
    if params or return_type:
        return params, return_type or UNKNOWN
    return None
