import unittest
from typing import Optional, Set

from . import utils

from hermes_gen.grammar import parse_grammar, Symbol
from hermes_gen.lalr1_automata import LALR1Automata, Node
from hermes_gen.counterexample.stateItem import StateItem


def _getSI(node: Node, ruleIdx: int) -> StateItem:
    return StateItem.getStateItem(node, node.rules[ruleIdx])


class TestCETables(unittest.TestCase):

    def _checkTrans(self, src: StateItem, symbol: Optional[Symbol], dst: Optional[StateItem]):
        if symbol is not None and dst is not None:
            self.assertEqual(symbol, src.transSymbol)
            self.assertEqual(dst, src.transItem)
            self.assertIn(src, dst.revTrans[symbol])
        else:
            self.assertIsNone(src.transSymbol)
            self.assertIsNone(src.transItem)

    def _checkProd(self, src: StateItem, exp: Set[StateItem]):
        self.assertEqual(len(src.fwdProd), len(exp))
        for x in exp:
            self.assertIn(x, src.fwdProd)

    def test_0_G10(self):
        testFile = utils.getTestFilename("G10.hm")
        grammar = parse_grammar(testFile)
        lalr = LALR1Automata(grammar)

        StateItem.initLookups(lalr)

        P = Symbol.get("P")
        E = Symbol.get("E")
        T = Symbol.get("T")
        ID = Symbol.get("id")
        openP = Symbol.get("open_p")
        closeP = Symbol.get("close_p")
        plus = Symbol.get("plus")

        n0 = lalr.nodes[0]
        n1 = lalr.nodes[1]
        n2 = lalr.nodes[2]
        n3 = lalr.nodes[3]
        n4 = lalr.nodes[4]
        n5 = lalr.nodes[5]
        n6 = lalr.nodes[6]
        n7 = lalr.nodes[7]
        n8 = lalr.nodes[8]

        n0r0 = _getSI(n0, 0)
        n0r1 = _getSI(n0, 1)
        n0r2 = _getSI(n0, 2)
        n0r3 = _getSI(n0, 3)
        n0r4 = _getSI(n0, 4)

        n1r0 = _getSI(n1, 0)
        n1r1 = _getSI(n1, 1)

        n2r0 = _getSI(n2, 0)

        n3r0 = _getSI(n3, 0)
        n3r1 = _getSI(n3, 1)

        n4r0 = _getSI(n4, 0)
        n4r1 = _getSI(n4, 1)
        n4r2 = _getSI(n4, 2)

        n5r0 = _getSI(n5, 0)
        n5r1 = _getSI(n5, 1)
        n5r2 = _getSI(n5, 2)
        n5r3 = _getSI(n5, 3)
        n5r4 = _getSI(n5, 4)

        n6r0 = _getSI(n6, 0)

        n7r0 = _getSI(n7, 0)
        n7r1 = _getSI(n7, 1)

        n8r0 = _getSI(n8, 0)

        # yapf: disable

        TRANS = [
            (n0r0, E, n1r0),
            (n0r1, E, n1r1),
            (n0r2, T, n2r0),
            (n0r3, ID, n3r0),
            (n0r4, ID, n3r1),

            (n1r0, None, None),
            (n1r1, plus, n4r0),

            (n2r0, None, None),

            (n3r0, openP, n5r0),
            (n3r1, None, None),

            (n4r0, T, n6r0),
            (n4r1, ID, n3r0),
            (n4r2, ID, n3r1),

            (n5r0, E, n7r0),
            (n5r1, E, n7r1),
            (n5r2, T, n2r0),
            (n5r3, ID, n3r0),
            (n5r4, ID, n3r1),

            (n6r0, None, None),

            (n7r0, closeP, n8r0),
            (n7r1, plus, n4r0),

            (n8r0, None, None)
        ]

        PROD = [
            (n0r0, {n0r1, n0r2}),
            (n0r1, {n0r1, n0r2}),
            (n0r2, {n0r3, n0r4}),
            (n0r3, set()),
            (n0r4, set()),

            (n1r0, set()),
            (n1r1, set()),

            (n2r0, set()),

            (n3r0, set()),
            (n3r1, set()),

            (n4r0, {n4r1, n4r2}),
            (n4r1, set()),
            (n4r2, set()),

            (n5r0, {n5r1, n5r2}),
            (n5r1, {n5r1, n5r2}),
            (n5r2, {n5r3, n5r4}),
            (n5r3, set()),
            (n5r4, set()),

            (n6r0, set()),

            (n7r0, set()),
            (n7r1, set()),

            (n8r0, set())
        ]

        n0RP = {
            E: {n0r0, n0r1},
            T: {n0r2}
        }

        n4RP = {
            T: {n4r0}
        }

        n5RP = {
            E: {n5r0, n5r1},
            T: {n5r2}
        }

        REV_PROD = [
            (n0r0, n0RP),
            (n0r1, n0RP),
            (n0r2, n0RP),
            (n0r3, n0RP),
            (n0r4, n0RP),

            (n1r0, {}),
            (n1r1, {}),

            (n2r0, {}),

            (n3r0, {}),
            (n3r1, {}),

            (n4r0, n4RP),
            (n4r1, n4RP),
            (n4r2, n4RP),

            (n5r0, n5RP),
            (n5r1, n5RP),
            (n5r2, n5RP),
            (n5r3, n5RP),
            (n5r4, n5RP),

            (n6r0, {}),

            (n7r0, {}),
            (n7r1, {}),

            (n8r0, {})
        ]
        # yapf: enable

        for x in TRANS:
            self._checkTrans(*x)

        for x in PROD:
            self._checkProd(*x)

        for si, x in REV_PROD:
            self.assertDictEqual(x, si.revProd, f'Failed for state item {str(si)}')

    def test_1_epsilon(self):
        testFile = utils.getTestFilename("epsilon.hm")
        grammar = parse_grammar(testFile)
        lalr = LALR1Automata(grammar)

        StateItem.initLookups(lalr)

        S = Symbol.get('S')
        A = Symbol.get('A')
        B = Symbol.get('B')
        a = Symbol.get('a')
        b = Symbol.get('b')

        n0 = lalr.nodes[0]
        n1 = lalr.nodes[1]
        n2 = lalr.nodes[2]
        n3 = lalr.nodes[3]
        n4 = lalr.nodes[4]

        n0r0 = _getSI(n0, 0)
        n0r1 = _getSI(n0, 1)
        n0r2 = _getSI(n0, 2)
        n0r3 = _getSI(n0, 3)

        n1r0 = _getSI(n1, 0)

        n2r0 = _getSI(n2, 0)
        n2r1 = _getSI(n2, 1)

        n3r0 = _getSI(n3, 0)

        n4r0 = _getSI(n4, 0)

        # yapf: disable
        TRANS = [
            (n0r0, A, n1r0),
            (n0r1, B, n2r0),
            (n0r2, B, n2r1),

            (n0r3, None, None),

            (n1r0, None, None),

            (n2r0, b, n3r0),
            (n2r1, a, n4r0),

            (n3r0, None, None),
            (n4r0, None, None)
        ]

        PROD = [
            (n0r0, {n0r1}),
            (n0r1, {n0r2, n0r3}),
            (n0r2, {n0r2, n0r3}),
            (n0r3, set()),

            (n1r0, set()),

            (n2r0, set()),
            (n2r1, set()),

            (n3r0, set()),

            (n4r0, set())
        ]

        n0RP = {
            A: {n0r0},
            B: {n0r1, n0r2}
            }

        REV_PROD = [
            (n0r0, n0RP),
            (n0r1, n0RP),
            (n0r2, n0RP),
            (n0r3, n0RP),

            (n1r0, {}),

            (n2r0, {}),
            (n2r1, {}),

            (n3r0, {}),

            (n4r0, {})
        ]
        # yapf: enable

        for x in TRANS:
            self._checkTrans(*x)

        for x in PROD:
            self._checkProd(*x)

        for si, x in REV_PROD:
            self.assertDictEqual(x, si.revProd, f'Failed for state item {str(si)}')
