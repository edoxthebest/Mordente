from pathlib import Path

from lark import Lark, ParseTree, ast_utils

from . import ast
from .ast import _POLICY


class Parser:
    def __init__(self) -> None:
        with open(Path(__file__).parent.absolute() / 'ifdif.lark') as grammar:
            self._parser = Lark(grammar, parser='lalr')
            self._transformer = ast_utils.create_transformer(ast, transformer=ast.ToAst())

    def parse(self, query: str) -> ParseTree:
        return self._parser.parse(query)

    def transform_query(self, parsed_query: ParseTree) -> _POLICY:
        return self._transformer.transform(parsed_query)

    def solve(self, query: str) -> _POLICY:
        parsed = self.parse(query)
        # print(parsed.pretty())
        ast = self.transform_query(parsed)
        return ast
