""" Parse typing information out of docstrings """

import re

if False:
    from typing import Optional, Dict, List, Union, Tuple


def parse_docstring(docstring):  # type: (str) -> Optional[Tuple[Dict[str, str], str]]
    """ Parse out typing information from docstring """
    return handle_google(docstring)


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
            params = dict(
                re.findall(
                    r"^{}[ \t]+([\w\-]+) *(?:\(([\w\-\[\]\., ]+)\) *):".format(
                        header_indent
                    ),
                    docstring[
                        header.end() : headers[i + 1].start()
                        if i < len(headers)
                        else len(docstring)
                    ],
                    re.M,
                )
            )
        elif header_name in ("yield", "yields", "return", "returns"):
            returns = re.search(
                r"^{}[ \t]+([\w\-\[\]\., ]+) *:".format(header_indent),
                docstring[header.end() :],
                re.M,
            )
            if returns:
                return_type = returns.group(1)
                if "yield" in header_name:
                    return_type = "typing.Iterable[{}]".format(return_type)
    if return_type:
        return params, return_type
    return None
