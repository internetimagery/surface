""" Useful utilities """

if False:
    from typing import *

import re
import time
import inspect
import logging
import importlib
import traceback
import sigtools  # type: ignore

LOG = logging.getLogger(__name__)

import_times = {}  # type: Dict[str, float]


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
    return re.sub(
        r"<(.+) at (0x[0-9A-Fa-f]+)>",
        r"<\1 at memory_address>",
        str(err),
    )


def get_signature(func):  # type: (Any) -> sigtools.Signature
    # handle bug in funcsigs
    restore_attr = False
    if hasattr(func, "__annotations__") and func.__annotations__ is None:
        func.__annotations__ = {}
        restore_attr = True
    try:
        return sigtools.signature(func)
    except (SyntaxError, ValueError) as err:
        LOG.debug("Error getting signature for {}".format(func))
        LOG.debug(traceback.format_exc())
        raise ValueError(str(err))
    finally:
        if restore_attr:
            func.__annotations__ = None


def get_source(func):  # type: (Any) -> str
    try:
        sig = get_signature(func)
    except ValueError:
        return ""
    sources = sorted(sig.sources["+depths"].items(), key=lambda s: s[1])
    try:
        return inspect.getsource(sources[-1][0]) or ""
    except IOError:
        pass
    except TypeError as err:
        LOG.debug(err)
    return ""
