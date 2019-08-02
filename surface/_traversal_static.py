""" Statically traverse the files source code, in tandem with live traversal """

if False:
    from typing import *

import ast
import tokenize
import collections


class Tokens(collections.Sequence):
    """ Helper methods to work with token stream """

    def __init__(self, source): # type: (str) -> None
        lines = iter(source.splitlines(True))
        reader = lambda: next(lines)
        self._tokens = tuple(tokenize.generate_tokens(reader))
        self._pos_map = {self._tokens[i][2]: i  for i in range(len(self._tokens))}

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._tokens[item]
        return self._tokens[self._pos_map[item]]

    def __len__(self):
        return len(self._tokens)


class Scope(object):

    _cache = {}

    def __init__(self):
        pass

    @classmethod
    def _get_map(cls, filename): # type: (str) -> Tuple[Any, Tokens]
        if filename not in cls._cache:
            with open(filename) as handle:
                contents = handle.read()
                module = ast.parse(contents, filename=filename)
                tokens = Tokens(contents)
                cls._cache[filename] = (module, tokens)
        return cls._cache[filename]
