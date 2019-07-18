""" Traverse an API heirarchy """


# TODO: import module by name
# TODO: get its global name, and path
# TODO: cache path names to module name for efficiency

# TODO: walk through everything it exposes at the top level
# TODO: eg: names not starting with underscores
# TODO: or anything in the __all__ variable.

# TODO: create a simplified representation of the signatures found (names and types)

# BONUS: collect type information as part of the signatures
# BONUS: traverse heirarchy for specified types, recursively getting their api
# BONUS: so later a type can be compared by value, not just name

import re
import os.path
import inspect
import sigtools
from surface._base import *

import_reg = re.compile(r"__init__\.(py[cd]?|so)$")


def recurse(name, path_filter=None):  # type: (str, Callable[[str], bool]) -> Set[str]
    """ Given a module path, return paths to its children. """

    stack = [name]
    paths = []

    while stack:
        import_name = stack.pop()
        module = __import__(import_name, fromlist=[""])
        paths.append(import_name)
        try:
            module_path = module.__file__
        except AttributeError:
            continue

        if not import_reg.search(module_path):
            paths.append(import_name)
            continue

        package = os.path.dirname(module_path)
        submodules = os.listdir(package)
        for submodule in submodules:
            if submodule.startswith("_"):
                pass
            elif submodule.endswith(".py"):
                paths.append("{}.{}".format(import_name, submodule[:-3]))
            elif os.path.isfile(os.path.join(package, submodule, "__init__.py")):
                stack.append("{}.{}".format(import_name, submodule))
    return paths


def traverse(obj):  # type: (Any) -> List[Any]
    """ Entry point to generating an API representation. """
    attributes = (attr for attr in inspect.getmembers(obj) if is_public(attr[0]))
    # __all__ attribute restricts import with *,
    # and displays what is intended to be public
    whitelist = getattr(obj, "__all__", [])
    if whitelist:
        attributes = (attr for attr in attributes if attr[0] in whitelist)

    # Sort the attributes by name for readability, and diff-ability (is that a word?)
    attributes = sorted(attributes, key=lambda a: a[0])

    # Walk the surface of the object, and extract the information
    for name, value in attributes:
        # TODO: How to ensure we find the original classes and methods, and not wrappers?
        # TODO: Handle recursive traversal.

        if inspect.ismodule(value):
            yield handle_module(name, value)
        elif inspect.isclass(value):
            yield handle_class(name, value)
        # Python2
        elif inspect.ismethod(value):
            yield handle_method(name, value)
        elif inspect.isfunction(value):
            # python3
            if inspect.isclass(obj):
                yield handle_method(name, value)
            else:
                yield handle_function(name, value)
        elif name != "__init__":
            yield handle_variable(name, value)


def handle_function(name, value):
    sig = sigtools.signature(value)
    return Func(
        name,
        tuple(
            Arg(
                n,
                "typing.Any",
                convert_arg_kind(str(p.kind))
                | (0 if p.default is sig.empty else DEFAULT),
            )
            for n, p in sig.parameters.items()
        ),
        "typing.Any",
    )


def handle_method(name, value):
    sig = sigtools.signature(value)
    params = list(sig.parameters.items())
    if not "@staticmethod" in inspect.getsource(value):
        params = params[1:]
    return Func(
        name,
        tuple(
            Arg(
                n,
                "typing.Any",
                convert_arg_kind(str(p.kind))
                | (0 if p.default is sig.empty else DEFAULT),
            )
            for n, p in params
        ),
        "typing.Any",
    )


def handle_class(name, value):
    return Class(name, tuple(traverse(value)))


def handle_variable(name, value):
    return Var(name, "typing.Any")


def handle_module(name, value):
    return Module(name, value.__name__, tuple(traverse(value)))


def is_public(name):
    return name == "__init__" or not name.startswith("_")


def convert_arg_kind(kind):
    if kind == "POSITIONAL_ONLY":
        return POSITIONAL
    if kind == "KEYWORD_ONLY":
        return KEYWORD
    if kind == "POSITIONAL_OR_KEYWORD":
        return POSITIONAL | KEYWORD
    if kind == "VAR_POSITIONAL":
        return POSITIONAL | VARIADIC
    if kind == "VAR_KEYWORD":
        return KEYWORD | VARIADIC
    raise TypeError("Unknown type.")
