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

import surface._utils as utils
from surface._base import TYPE_CHARS

LOG = logging.getLogger(__name__)

func_header_reg = re.compile(r"^[ \t]*(def \w+)", re.M)
type_comment_reg = re.compile(r"# +type: ({})".format(TYPE_CHARS))
type_comment_sig_reg = re.compile(r"# +type: \(({0})?\) +-> +({0})".format(TYPE_CHARS))


class StaticMap(object):
    def __init__(self, tokens, token_map, func):
        self._tokens = tokens
        self._token_map = token_map
        self._func = func

    @classmethod
    def parse(cls, source):
        header = func_header_reg.match(source)
        if not header:
            return None
        source = source[header.start(1) :]

        # Parse source code
        lines = iter(source.splitlines(True))
        try:
            tokens = list(tokenize.generate_tokens(lambda: next(lines)))
        except tokenize.TokenError:
            LOG.debug(traceback.format_exc())
            return None
        func = ast.parse(source).body[0]
        token_map = {tokens[i][2]: i for i in range(len(tokens))}
        return cls(tokens, token_map, func)

    def get_signature(self):
        body = self._func.body[0]
        body_index = self._token_map[body.lineno, body.col_offset]
        sig_comment = self._tokens[body_index - 3]
        if sig_comment[0] != tokenize.COMMENT:
            return None
        sig_match = type_comment_sig_reg.match(sig_comment[1])
        if not sig_match:
            return None
        return (sig_match.group(1) or "").strip(), sig_match.group(2).strip()

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

    mapping = StaticMap.parse(source)
    if not mapping:
        return None

    # Locate function signature type
    sig_parts = mapping.get_signature()
    if not sig_parts:
        return None
    param_comment, return_comment = sig_parts

    # Normalize return_type
    context = func.__globals__
    return_type = utils.normalize_type(return_comment, context)

    if not param_comment:  # No parameters, nothing more to do.
        return {}, return_type

    return None
    # Parse signature
    if param_comment != "...":
        param_ast = ast.parse(param_comment).body[0].value  # type: ignore
        if isinstance(param_ast, ast.Tuple) and param_ast.elts:
            params = [
                str(
                    param_comment[
                        param_ast.elts[i].col_offset : param_ast.elts[i + 1].col_offset
                    ]
                )
                .rsplit(",", 1)[0]
                .strip()
                for i in range(len(param_ast.elts) - 1)
            ]
            params.append(str(param_comment[param_ast.elts[-1].col_offset :].strip()))
        else:
            params = [str(param_comment)]
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
