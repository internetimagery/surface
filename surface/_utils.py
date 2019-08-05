""" Useful utilities """

if False:
    from typing import *

import re
import time
import logging
import importlib

# try:
#     from inspect import signature  # type: ignore
# except ImportError:
#     from funcsigs import signature  # type: ignore

from sigtools import signature  # type: ignore

LOG = logging.getLogger(__name__)

import_times = {}  # type: Dict[str, float]


def import_module(name):
    start = time.time()
    try:
        LOG.debug("Importing: {}".format(name))
        return importlib.import_module(name)
    finally:
        if name not in import_times:
            import_times[name] = time.time() - start


def clean_err(err):
    """ Strip out memory parts of an error """
    return re.sub(
        r"<([\w\.]+) object at (0x[\da-zA-Z]+)>",
        r"<\1 object at memory_address>",
        str(err),
    )


def get_signature(func):
    # handle bug in funcsigs
    restore_attr = False
    if hasattr(func, "__annotations__") and func.__annotations__ is None:
        func.__annotations__ = {}
        restore_attr = True
    try:
        return signature(func)
    finally:
        if restore_attr:
            func.__annotations__ = None
