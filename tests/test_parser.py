import unittest

from selinuxtool.ifdif.ast import _POLICY, And, BDiamond, Diamond, Not, TruePolicy, UpArrow
from selinuxtool.ifdif.parser import Parser


class TestPolicyParser(unittest.TestCase):
    def setUp(self) -> None:
        self._parser = Parser()

    def test_parse_true(self) -> None:
        parsed = self._parser.parse('(true)')
        ast = self._parser.transform_query(parsed)

        self.assertEqual(parsed.data, 'true')
        self.assertIsInstance(ast, TruePolicy)

    def test_parse_up_arrow(self) -> None:
        parsed = self._parser.parse('label_1 (testLabel)')
        ast: UpArrow = self._parser.transform_query(parsed)

        self.assertEqual(parsed.data, 'up_arrow')
        self.assertEqual(parsed.children[0].children[0], '1')
        self.assertEqual(parsed.children[1].children[0], 'testLabel')
        self.assertIsInstance(ast, UpArrow)
        self.assertIsInstance(ast.index, int)
        self.assertIsInstance(ast.label, str)
        self.assertEqual(ast.index, 1)
        self.assertEqual(ast.label, 'testLabel')

    def test_parse_and(self) -> None:
        parsed = self._parser.parse('true and true')
        ast: And = self._parser.transform_query(parsed)

        self.assertEqual(parsed.data, 'and')
        self.assertIsInstance(ast, And)
        self.assertIsInstance(ast.left, _POLICY)
        self.assertIsInstance(ast.right, _POLICY)

    def test_parse_not(self) -> None:
        parsed = self._parser.parse('not true')
        ast: Not = self._parser.transform_query(parsed)

        self.assertEqual(parsed.data, 'not')
        self.assertIsInstance(ast, Not)
        self.assertIsInstance(ast.inner, _POLICY)

    def test_parse_diamond(self) -> None:
        parsed = self._parser.parse('ito_2 (true)')
        ast: Diamond = self._parser.transform_query(parsed)

        self.assertEqual(parsed.data, 'diamond')
        self.assertEqual(parsed.children[0].children[0], '2')
        self.assertIsInstance(ast, Diamond)
        self.assertIsInstance(ast.index, int)
        self.assertIsInstance(ast.policy, _POLICY)
        self.assertEqual(ast.index, 2)

    def test_parse_bdiamond(self) -> None:
        parsed = self._parser.parse('ifrom_2 true')
        ast: BDiamond = self._parser.transform_query(parsed)

        self.assertEqual(parsed.data, 'b_diamond')
        self.assertEqual(parsed.children[0].children[0], '2')
        self.assertIsInstance(ast, BDiamond)
        self.assertIsInstance(ast.index, int)
        self.assertIsInstance(ast.policy, _POLICY)
        self.assertEqual(ast.index, 2)
