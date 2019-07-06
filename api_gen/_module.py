""" Map paths to module names """

import sys
import os.path

if sys.version_info.major == 3:
    from typing import Iterable, Dict, Tuple

__all__ = ["map_modules"]


def get_abs_module(base):  # type: (str) -> str
    """ Given a path. Walk upwards to get full name """
    if os.path.isfile(base):
        name = os.path.splitext(os.path.basename(base))[0]
        modulepath = [] if name == "__init__" else [name]
        base = os.path.dirname(base)
    else:
        modulepath = []
    while True:
        root = os.path.dirname(base)
        if root == base:
            break
        elif "__init__.py" in os.listdir(base):
            modulepath.append(os.path.basename(base))
            base = root
        else:
            break
    modulepath.sort(reverse=True)
    return ".".join(modulepath)


def get_sub_module(root):  # type: (str) -> Iterable[Tuple[str, str]
    """ Given a directory, descend getting relative module names """
    for filename in os.listdir(root):
        filepath = os.path.join(root, filename)
        if os.path.isdir(filepath):  # Descend further
            for name, childpath in get_sub_module(filepath):
                yield "{}.{}".format(filename, name) if name else filename, childpath
        else:
            name, ext = os.path.splitext(filename)
            if ext != ".py":
                continue
            if name == "__init__":
                name = ""
            yield (name, filepath)


def map_modules(sources):  # type: (Iterable[str]) -> Dict[str, str]
    """ Discover and map module names to paths
    """
    name_to_path = {}
    for source in sources:
        if os.path.isfile(source):
            name = get_abs_module(source)
            if name:
                name_to_path[name] = source
        elif os.path.isdir(source):
            root = get_abs_module(source)
            for name, filepath in get_sub_module(source):
                name_to_path["{}.{}".format(root, name) if root else name] = filepath
    return name_to_path
