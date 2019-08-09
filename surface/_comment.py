""" Parse typing comments """

if False:  # type checking
    from typing import *

import re
import ast
import token
import logging
import inspect
import tokenize
import traceback
import collections

from surface._utils import normalize_type, get_signature, get_tokens
from surface._base import TYPE_CHARS

LOG = logging.getLogger(__name__)

func_header_reg = re.compile(r"^[ \t]*(def \w+)", re.M)
type_comment_reg = re.compile(r"# +type: ({})".format(TYPE_CHARS))
type_comment_sig_reg = re.compile(r"# +type: \(({0})?\) +-> +({0})".format(TYPE_CHARS))


class Static(object):
    def __init__(
        self, tokens, token_map, ast
    ):  # type: (Sequence[Any], Dict[Tuple[int, int], int], Any) -> None
        self._tokens = tokens
        self._token_map = token_map
        self._ast = ast

    @classmethod
    def parse(cls, source):  # type: (str) -> Optional[Static]
        header = func_header_reg.match(source)
        if not header:
            return None
        source = source[header.start(1) :]

        # Parse source code
        tokens = get_tokens(source)
        if not tokens:
            return None
        try:
            parsed_ast = ast.parse(source).body[0]
        except SyntaxError:
            return None
        token_map = {tokens[i][2]: i for i in range(len(tokens))}
        return cls(tokens, token_map, parsed_ast)

    def get_signature(self):  # type: () -> Optional[Tuple[str, str]]
        body = self._ast.body[0]
        # Silly hack to get around ast inconsistencies
        # Walk the token stream till we hit the first token on the first line
        # of the body of the function.
        # Then walk backwards from there till we hit the end of the function.
        # If we spot a comment between now and then, sweet. Otherwise nothing to do!
        for i, tok in enumerate(self._tokens):
            if tok[2][0] == body.lineno:
                break
        else:
            return None
        for j in range(i, 0, -1):
            tok = self._tokens[j]
            if tok[0] == token.OP and tok[1] == ":":
                return None
            if tok[0] == tokenize.COMMENT:
                break
        else:
            return None
        sig_match = type_comment_sig_reg.match(tok[1])
        if not sig_match:
            return None
        return (sig_match.group(1) or "").strip(), sig_match.group(2).strip()

    def get_params(self):  # type: () -> Optional[List[str]]
        # TODO: fill this out
        return None

    @property
    def has_external_types(self):
        return isinstance(self._ast, ast.Elipsis)

    # def iter_func(
    #     self, funcDef
    # ):  # type: (ast.FunctionDef) -> Iterable[Tuple[name, Tuple[int, int]]]
    #     for arg in funcDef.args.args:
    #         yield arg.arg, (arg.lineno, arg.col_offset)


def get_comment(func):  # type: (Any) -> Optional[Tuple[Dict[str, str], str]]
    try:
        source = inspect.getsource(func)
    except (IOError, TypeError) as err:
        LOG.debug(traceback.format_exc())
        return None
    if not source:
        return None

    mapping = Static.parse(source)
    if not mapping:
        return None

    # Locate function signature type
    sig_parts = mapping.get_signature()
    if not sig_parts:
        return None
    param_comment, return_comment = sig_parts

    # Normalize return_type
    context = func.__globals__
    return_type = normalize_type(return_comment, context)

    if not param_comment:  # No parameters, nothing more to do.
        return {}, return_type

    param_map = Static.parse(param_comment)
    if not param_map:
        return None

    if param_map.has_external_types:
        # Individual parameters must have typing...
        return None

    else:
        # Match parameters to function values
        params = param_map.get_params()
        return None

        # param_ast = ast.parse(param_comment).body[0].value  # type: ignore
        # if isinstance(param_ast, ast.Tuple) and param_ast.elts:
        #     params = [
        #         str(
        #             param_comment[
        #                 param_ast.elts[i].col_offset : param_ast.elts[i + 1].col_offset
        #             ]
        #         )
        #         .rsplit(",", 1)[0]
        #         .strip()
        #         for i in range(len(param_ast.elts) - 1)
        #     ]
        #     params.append(str(param_comment[param_ast.elts[-1].col_offset :].strip()))
        # else:
        #     params = [str(param_comment)]
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    # print(source)
    # print(sig_match.group(0))
    #
    # params = []
    # sig_comment = None
    # in_sig = False
    #
    # for i, tok in enumerate(tokens):
    #     if not in_sig and tok[0] == token.NAME and tok[1] == "def":
    #         in_sig = True
    #     elif in_sig and tok[0] == token.NEWLINE and i < len(tokens) - 1:
    #         sig_comment = sig_comment or type_comment_sig_reg.match(tokens[i + 1][1])
    #         break
    #     elif in_sig and tok[0] == tokenize.COMMENT:
    #         param = type_comment_reg.match(tok[1])
    #         if param:
    #             params.append(str(param.group(1).strip()))
    #         sig_comment = sig_comment or type_comment_sig_reg.match(tok[1])
    # if not sig_comment:
    #     return None
    #
    # # Validate the same number of params as comment params? Assume mypy etc will do it for us?
    #
    # return_type = sig_comment.group(2)
    # param_comment = sig_comment.group(1).strip()
    # if param_comment and param_comment != "...":
    #     param_ast = ast.parse(param_comment).body[0].value  # type: ignore
    #     if isinstance(param_ast, ast.Tuple) and param_ast.elts:
    #         params = [
    #             str(
    #                 param_comment[
    #                     param_ast.elts[i].col_offset : param_ast.elts[i + 1].col_offset
    #                 ]
    #             )
    #             .rsplit(",", 1)[0]
    #             .strip()
    #             for i in range(len(param_ast.elts) - 1)
    #         ]
    #         params.append(
    #             str(param_comment[param_ast.elts[-1].col_offset :].strip())
    #         )
    #     else:
    #         params = [str(param_comment)]
    # if return_type:
    #     return params, str(return_type)
    #
    # return None
