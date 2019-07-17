from surface._traversal import traverse, recurse
from surface._base import (
    POSITIONAL,
    KEYWORD,
    VARIADIC,
    DEFAULT,
    Var,
    Arg,
    Func,
    Class,
    Module,
)


def get_api(name):  # type: (str) -> Tuple[Any, ...]
    """
        Get a representation of the provided publicly exposed API.

        Args:
            name (str): path to module. eg mymodule.submodule

        Returns:
            Tuple[Any, ...]: Representation of API
    """
    mod = __import__(name, fromlist=[""])
    API = traverse(mod)
    return tuple(API)


def format_api(api, indent=""):  # type: (Iterable[Any], str) -> str
    """ Format api into an easier to read representation """
    result = ""
    for item in api:
        if isinstance(item, (Class, Module)) and item.body:
            result += indent + "{}(name='{}',body=(\n".format(
                item.__class__.__name__, item.name
            )
            result += format_api(item.body, indent + "    ")
            result += indent + ")\n"
        elif isinstance(item, Func) and item.args:
            result += indent + "Func(name='{}', args=(\n".format(item.name)
            result += format_api(item.args, indent + "    ")
            result += "{}), returns={})\n".format(indent, item.returns)

        else:
            result += indent + str(item) + "\n"
    return result
