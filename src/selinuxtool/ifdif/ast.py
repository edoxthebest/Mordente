from dataclasses import dataclass

from lark import Transformer, ast_utils, v_args

from selinuxtool.android.policy import SecurityLvl


class _IFDIF_AST(ast_utils.Ast):
    pass


class _POLICY(_IFDIF_AST):
    pass


@dataclass
class TruePolicy(_POLICY):
    pass


@dataclass
class UpArrow(_POLICY):
    index: int
    label: SecurityLvl | str


@dataclass
class And(_POLICY):
    left: _POLICY
    right: _POLICY


@dataclass
class Not(_POLICY):
    inner: _POLICY


@dataclass
class Diamond(_POLICY):
    index: int
    policy: _POLICY


@dataclass
class BDiamond(_POLICY):
    index: int
    policy: _POLICY


class ToAst(Transformer):
    def true(self, _: str) -> TruePolicy:
        return TruePolicy()

    @v_args(inline=True)
    def index(self, i: int) -> int:
        return int(i)

    @v_args(inline=True)
    def label(self, s: str) -> SecurityLvl | str:
        try:
            return SecurityLvl[s]
        except KeyError:
            return str(s)
