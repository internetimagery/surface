""" Parse typing comments """

if False:  # type checking
    from typing import *

    M = TypeVar("M", bound="Mapper")

import re
import ast
import token
import logging
import inspect
import tokenize
import traceback
import collections

from surface._utils import normalize_type, get_signature, get_tokens
from surface._base import TYPE_CHARS, UNKNOWN

LOG = logging.getLogger(__name__)

func_header_reg = re.compile(r"^[ \t]*(def \w+)", re.M)
type_comment_reg = re.compile(r"# +type: ({})".format(TYPE_CHARS))
type_comment_sig_reg = re.compile(r"# +type: \(({0})?\) +-> +({0})".format(TYPE_CHARS))


class Mapper(object):
    def __init__(
        self, tokens, token_map, ast
    ):  # type: (Sequence[Any], Dict[Tuple[int, int], int], Any) -> None
        self._tokens = tokens
        self._token_map = token_map
        self._ast = ast

    @classmethod
    def parse(
        cls,  # type: Type[M]
        source,  # type: str
    ):  # type: (...) -> Optional[M]
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


class FuncMapper(Mapper):
    @classmethod
    def parse(
        cls,  # type: Type[M]
        source,  # type: str
    ):  # type: (...) -> Optional[M]
        header = func_header_reg.search(source)
        if not header:
            return None
        source = source[header.start(1) :]
        try:
            mapper = super(FuncMapper, cls).parse(source)
        except Exception as err:
            import pdb

            pdb.set_trace()
        return mapper

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

    def get_params(self):  # type: () -> Dict[str, str]
        arg_node = self._ast.args
        all_args = all_args = (
            arg_node.args
            + (arg_node.vararg or [])
            + getattr(arg_node, "kwonlyargs", [])
            + (arg_node.kwarg or [])
        )
        arg_tokens = [self._token_map[arg.lineno, arg.col_offset] for arg in all_args]
        params = {}
        i = 0
        for i in range(len(arg_tokens) - 1):
            start_index = arg_tokens[i]
            start_name = self._tokens[start_index][1]
            end_index = arg_tokens[i + 1]
            params[start_name] = (
                self._get_comment_inline(self._tokens[start_index:end_index]) or UNKNOWN
            )
        start_index = arg_tokens[i + 1]
        start_name = self._tokens[start_index][1]
        params[start_name] = (
            self._get_comment_inline(self._tokens[start_index:]) or UNKNOWN
        )
        return params

    def _get_comment_inline(self, tokens):  # type: (Any) -> Optional[str]
        for tok in tokens:
            if tok[0] == tokenize.NL:
                return None
            if tok[0] == tokenize.COMMENT:
                tok_match = type_comment_reg.match(tok[1])
                if tok_match:
                    return tok_match.group(1)
        return None


class ArgMapper(Mapper):
    def get_params(self):  # type: () -> List[str]
        node = self._ast.value
        # Single variable can just return
        if not isinstance(node, ast.Tuple):
            return [tokenize.untokenize(self._tokens).decode("utf8").strip()]

        params = []
        for i in range(len(node.elts) - 1):
            start_node = node.elts[i]
            end_node = node.elts[i + 1]
            start_index = self._token_map[start_node.lineno, start_node.col_offset]
            end_index = self._token_map[end_node.lineno, end_node.col_offset] - 1
            params.append(
                tokenize.untokenize(self._tokens[start_index:end_index]).strip()
            )
        params.append(tokenize.untokenize(self._tokens[end_index + 1 :]).strip())
        return params


def get_comment(func):  # type: (Any) -> Optional[Tuple[Dict[str, str], str]]
    if not inspect.isfunction(func) and not inspect.ismethod(func):
        # Classes should be handled, but are not yet...
        # Handling them would involve determining if they use __new__ or __init__
        # and using that as the function itself.
        return None

    try:
        source = inspect.getsource(func)
    except (IOError, TypeError) as err:
        LOG.debug(traceback.format_exc())
        return None
    if not source:
        return None

    func_map = FuncMapper.parse(source)
    if not func_map:
        return None

    # Locate function signature type
    sig_parts = func_map.get_signature()
    if not sig_parts:
        return None
    param_comment, return_comment = sig_parts

    # Normalize return_type
    context = func.__globals__
    return_type = normalize_type(return_comment, context)

    if not param_comment:  # No parameters, nothing more to do.
        return {}, return_type

    if param_comment == "...":  # We have external typing
        # Individual parameters must have typing...
        params = {
            name: normalize_type(typ, context)
            for name, typ in func_map.get_params().items()
        }
        return params, return_type

    else:
        param_map = ArgMapper.parse(param_comment)
        if not param_map:
            return None
        # Match parameters to function values
        sig = get_signature(func)
        if not sig:
            return None
        # reverse args, as a hack to skip "self" without knowing if it's an unbound method
        param_names = reversed(sig.parameters.keys())
        param_types = reversed(param_map.get_params())

        params = {
            name: normalize_type(typ, context)
            for name, typ in zip(param_names, param_types)
        }
        return params, return_type
