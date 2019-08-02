""" Useful utilities """

import re


def clean_err(err):
    """ Strip out memory parts of an error """
    return re.sub(
        r"<([\w\.]+) object at (0x[\da-zA-Z]+)>",
        r"<\1 object at memory_address>",
        str(err),
    )
