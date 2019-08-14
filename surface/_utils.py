""" Useful utilities and python compatability work arounds """

if False:
    from typing import *

import re
import sys
import ast
import time
import types
import inspect
import logging
import tokenize
import importlib
import traceback
import sigtools  # type: ignore

from surface._base import UNKNOWN, TYPING_ATTRS

LOG = logging.getLogger(__name__)

import_times = {}  # type: Dict[str, float]

# Cache stuff
cache_sig = {}  # type: Dict[int, sigtools.Signature]


def import_module(name):  # type: (str) -> Any
    start = time.time()
    try:
        LOG.debug("Importing: {}".format(name))
        return importlib.import_module(name)
    finally:
        if name not in import_times:
            import_times[name] = time.time() - start


def clean_repr(err):  # type: (Any) -> str
    """ Strip out memory parts of an error """
    return re.sub(r"<(.+) at (0x[0-9A-Fa-f]+)>", r"<\1 at memory_address>", str(err))


def get_signature(func):  # type: (Any) -> Optional[sigtools.Signature]
    func_id = id(func)
    if func_id in cache_sig:
        return cache_sig[func_id]

    # handle bug in funcsigs
    restore_attr = False
    if hasattr(func, "__annotations__") and func.__annotations__ is None:
        func.__annotations__ = {}
        restore_attr = True
    try:
        cache_sig[func_id] = sigtools.signature(func)
    except (SyntaxError, ValueError) as err:
        LOG.debug("Error getting signature for {}".format(func))
        LOG.debug(traceback.format_exc())
        return None
    else:
        return cache_sig[func_id]
    finally:
        if restore_attr:
            func.__annotations__ = None


def get_source(func):  # type: (Any) -> str
    try:
        sig = get_signature(func)
    except ValueError:
        return ""
    if not sig:
        return ""
    sources = sorted(sig.sources["+depths"].items(), key=lambda s: s[1])
    try:
        return inspect.getsource(sources[-1][0]) or ""
    except IOError:
        pass
    except TypeError as err:
        LOG.debug(err)
    return ""


def get_tokens(source):  # type: (str) -> List[tokenize.TokenInfo]
    try:
        if sys.version_info.major == 2:
            lines_str = (line for line in source.splitlines(True))
            tokens = list(tokenize.generate_tokens(lambda: next(lines_str)))
        else:
            lines_bytes = (line.encode("utf-8") for line in source.splitlines(True))
            tokens = list(tokenize.tokenize(lambda: next(lines_bytes)))
    except tokenize.TokenError:
        LOG.debug(traceback.format_exc())
        return []
    return tokens


def normalize_type(type_string, context):  # type: (str, Dict[str, Any]) -> str
    try:
        root = ast.parse(type_string).body[0].value  # type: ignore
    except (SyntaxError, AttributeError, IndexError):
        return UNKNOWN

    updates = {}
    stack = [root]
    while stack:
        node = stack.pop()

        # eg: myVariable
        if isinstance(node, ast.Name):
            parent = context.get(node.id)  # in scope?
            if parent:
                mod = inspect.getmodule(parent)
                if mod:
                    updates[node.col_offset] = mod.__name__
            elif node.id in TYPING_ATTRS:  # special case for typing
                updates[node.col_offset] = "typing"

        # eg: List[something] or Dict[str, int]
        elif isinstance(node, ast.Subscript):
            stack.append(node.value)
            stack.append(node.slice.value)  # type: ignore

        # eg: val1, val2
        elif isinstance(node, ast.Tuple):
            stack.extend(node.elts)

        # eg: val1.val2
        elif isinstance(node, ast.Attribute):
            stack.append(node.value)

    if updates:
        for i in sorted(updates.keys(), reverse=True):
            type_string = "{}{}.{}".format(type_string[:i], updates[i], type_string[i:])
    return type_string
