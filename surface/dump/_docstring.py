""" Parse typing information out of docstrings """

if False:  # type checking
    from typing import *

import re
import inspect
import itertools
import collections


TYPE_CHARS = r"\w[\w\.]*(?:\[[\w\.\[\]\,\s]+\])?"


def parse_docstring(docstring):
    # type: (str) -> Optional[Tuple[Dict[str, str], str]]
    """ Parse out typing information from docstring """
    result = handle_google(docstring)
    return result


HEADER_ARGS = ("arg", "args", "arguments", "parameters")
HEADER_RETURNS = ("yield", "yields", "return", "returns")
HEADER_REG = re.compile(
    r"^([ \t]*)({}):\s*$".format(
        "|".join(itertools.chain(HEADER_ARGS, HEADER_RETURNS))
    ),
    re.M | re.I,
)


def handle_google(docstring):  # type: (str) -> Optional[Tuple[Dict[str, str], str]]
    # Find the first header, to establish indent
    headers = list(HEADER_REG.finditer(docstring))
    if not headers or len(headers) > 2:
        return None

    params = collections.OrderedDict()
    returns = None

    for i, header in enumerate(headers):
        if header.group(2).lower() in HEADER_ARGS:
            # Search args
            for param in re.finditer(
                r"^{}[ \t]+([\w\-]+) *\((?::\w+:)?`*({})`*\)(?: *: .+| *)$".format(
                    header.group(1), TYPE_CHARS
                ),
                docstring[
                    header.end() : headers[i + 1].start()
                    if i < len(headers) - 1
                    else len(docstring)
                ],
                re.M,
            ):
                params[param.group(1)] = param.group(2).strip()
            if not params:
                # If we have an Args section, and nothing inside it... we are likely looking at a non-google style docstring
                return None
        elif header.group(2).lower() in HEADER_RETURNS:
            # search returns
            match = re.search(
                r"^{}[ \t]+(?::\w+:)?`*({})`*(?: *: .+| *)$".format(header.group(1), TYPE_CHARS),
                docstring[
                    header.end() : headers[i + 1].start()
                    if i < len(headers) - 1
                    else len(docstring)
                ],
                re.M,
            )
            if match:
                return_type = match.group(1)
                if "yield" in header.group(2):
                    return_type = "typing.Iterable[{}]".format(return_type)
                returns = return_type
    if not params and not returns:
        # If we have no params, and no returns (but discovered headers earlier so would expect either of these)
        # then this likely was not a google formatted docstring.
        return None
    return params, returns or "typing.Any"
