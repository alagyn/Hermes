import unittest
from typing import List

from . import utils

from hermes_gen.lalr1_automata import Node, AnnotRule, LALR1Automata
from hermes_gen.grammar import Grammar, Rule, parse_grammar, Symbol
from hermes_gen.consts import END


class TestLALRClosure(unittest.TestCase):

    def _checkNodes(self, expNodes: List[Node], actNodes: List[Node]):
        for exp, act in zip(expNodes, actNodes):
            for expRule, actRule in zip(exp.rules, act.rules):
                self.assertEqual(expRule, actRule, f"{exp} Rule not equal\n\tExp: {expRule}\n\tAct: {actRule}")

        self.assertEqual(len(expNodes), len(actNodes))

    def _checkTransitions(self, expNodes: List[Node], actNodes: List[Node]):
        for exp, act in zip(expNodes, actNodes):
            self.assertDictEqual(exp.trans, act.trans)

    def test_0_node_combine(self):
        Symbol.reset()
        SP = Symbol('S_PRIME', "", False)
        S = Symbol('S', "", False)
        X = Symbol('X', "", False)
        a = Symbol('a', "a", False)
        b = Symbol('b', "b", False)

        r0 = Rule(1, SP, [S], "", 0, 0)
        r1 = Rule(2, S, [X, X], "", 0, 0)
        r2 = Rule(3, X, [a, X], "", 0, 0)

        n0 = Node(0)
        n0.addRule(r0, 0, {Symbol.END_SYMBOL})
        n0.addRule(r1, 1, {Symbol.END_SYMBOL})
        n0.addRule(r2, 0, {a, Symbol.END_SYMBOL})

        n1 = Node(1)
        n1.addRule(r0, 0, {a, Symbol.END_SYMBOL})
        n1.addRule(r1, 1, {b})
        n1.addRule(r2, 0, {a, b})

        n0.combine(n1)

        expNode = Node(2)
        expNode.addRule(r0, 0, {a, Symbol.END_SYMBOL})
        expNode.addRule(r1, 1, {b, Symbol.END_SYMBOL})
        expNode.addRule(r2, 0, {a, b, Symbol.END_SYMBOL})

        self.assertEqual(expNode, n0)

    def test_1_LALR1(self):
        testfile = utils.getTestFilename('LALR1Test.hm')
        grammar = parse_grammar(testfile)

        lalr = LALR1Automata(grammar)

        SP = Symbol.get('S_PRIME')
        S = Symbol.get('S')
        X = Symbol.get('X')
        a = Symbol.get('a')
        b = Symbol.get('b')

        r0 = Rule(1, SP, [S], "", 0, 0)
        r1 = Rule(2, S, [X, X], "", 0, 0)
        r2 = Rule(3, X, [a, X], "", 0, 0)
        r3 = Rule(4, X, [b], "", 0, 0)

        n0 = Node(0)
        n0.addRule(r0, 0, {Symbol.END_SYMBOL})
        n0.addRule(r1, 0, {Symbol.END_SYMBOL})
        n0.addRule(r2, 0, {a, b})
        n0.addRule(r3, 0, {a, b})

        n1 = Node(1)
        n1.addRule(r0, 1, {Symbol.END_SYMBOL})

        n2 = Node(2)
        n2.addRule(r1, 1, {Symbol.END_SYMBOL})
        n2.addRule(r2, 0, {Symbol.END_SYMBOL})
        n2.addRule(r3, 0, {Symbol.END_SYMBOL})

        n36 = Node(3)
        n36.addRule(r2, 1, {a, b, Symbol.END_SYMBOL})
        n36.addRule(r2, 0, {a, b, Symbol.END_SYMBOL})
        n36.addRule(r3, 0, {a, b, Symbol.END_SYMBOL})

        n5 = Node(4)
        n5.addRule(r1, 2, {Symbol.END_SYMBOL})

        n47 = Node(5)
        n47.addRule(r3, 1, {a, b, Symbol.END_SYMBOL})

        n89 = Node(6)
        n89.addRule(r2, 2, {a, b, Symbol.END_SYMBOL})

        EXP_NODES = [n0, n1, n2, n36, n47, n5, n89]

        self._checkNodes(EXP_NODES, lalr.nodes)

    def test_2_G10(self):
        testfile = utils.getTestFilename("G10.hm")
        grammar = parse_grammar(testfile)

        lalr = LALR1Automata(grammar)

        P = Symbol.get("P")
        E = Symbol.get("E")
        T = Symbol.get("T")
        _id = Symbol.get('id')
        plus = Symbol.get("plus")
        open_p = Symbol.get("open_p")
        close_p = Symbol.get("close_p")

        r1 = Rule(1, P, [E], "", 0, 0)
        r2 = Rule(2, E, [E, plus, T], "", 0, 0)
        r3 = Rule(3, E, [T], "", 0, 0)
        r4 = Rule(4, T, [_id, open_p, E, close_p], "", 0, 0)
        r5 = Rule(5, T, [_id], "", 0, 0)

        n0 = Node(0)
        n0.addRule(r1, 0, {Symbol.END_SYMBOL})
        n0.addRule(r2, 0, {plus, Symbol.END_SYMBOL})
        n0.addRule(r3, 0, {plus, Symbol.END_SYMBOL})
        n0.addRule(r4, 0, {plus, Symbol.END_SYMBOL})
        n0.addRule(r5, 0, {plus, Symbol.END_SYMBOL})

        n1 = Node(1)
        n1.addRule(r1, 1, {Symbol.END_SYMBOL})
        n1.addRule(r2, 1, {plus, Symbol.END_SYMBOL})

        n2 = Node(2)
        n2.addRule(r3, 1, {plus, close_p, Symbol.END_SYMBOL})

        n3 = Node(3)
        n3.addRule(r4, 1, {plus, close_p, Symbol.END_SYMBOL})
        n3.addRule(r5, 1, {plus, close_p, Symbol.END_SYMBOL})

        n4 = Node(4)
        n4.addRule(r2, 2, {plus, close_p, Symbol.END_SYMBOL})
        n4.addRule(r4, 0, {plus, close_p, Symbol.END_SYMBOL})
        n4.addRule(r5, 0, {plus, close_p, Symbol.END_SYMBOL})

        n5 = Node(5)
        n5.addRule(r4, 2, {plus, close_p, Symbol.END_SYMBOL})
        n5.addRule(r2, 0, {plus, close_p})
        n5.addRule(r3, 0, {plus, close_p})
        n5.addRule(r4, 0, {plus, close_p})
        n5.addRule(r5, 0, {plus, close_p})

        n6 = Node(6)
        n6.addRule(r2, 3, {plus, close_p, Symbol.END_SYMBOL})

        n7 = Node(7)
        n7.addRule(r4, 3, {plus, close_p, Symbol.END_SYMBOL})
        n7.addRule(r2, 1, {plus, close_p})

        n8 = Node(8)
        n8.addRule(r4, 4, {plus, close_p, Symbol.END_SYMBOL})

        EXP_NODES = [n0, n1, n2, n3, n4, n5, n6, n7, n8]

        self._checkNodes(EXP_NODES, lalr.nodes)

        n0.addTrans(E, n1)
        n0.addTrans(T, n2)
        n0.addTrans(_id, n3)

        n1.addTrans(plus, n4)

        n3.addTrans(open_p, n5)

        n4.addTrans(T, n6)
        n4.addTrans(_id, n3)

        n5.addTrans(T, n2)
        n5.addTrans(_id, n3)
        n5.addTrans(E, n7)

        n7.addTrans(close_p, n8)
        n7.addTrans(plus, n4)

        self._checkTransitions(EXP_NODES, lalr.nodes)

    def test_3_epsilon(self):
        testfile = utils.getTestFilename("epsilon.hm")
        grammar = parse_grammar(testfile)
        lalr = LALR1Automata(grammar)

        S = Symbol.get("S")
        A = Symbol.get("A")
        B = Symbol.get("B")
        a = Symbol.get("a")
        b = Symbol.get("b")

        r0 = Rule(0, S, [A], "", 0, 0)
        r1 = Rule(1, A, [B, b], "", 0, 0)
        r2 = Rule(2, B, [B, a], "", 0, 0)
        r3 = Rule(3, B, [], "", 0, 0)

        n0 = Node(0)
        n0.addRule(r0, 0, {Symbol.END_SYMBOL})
        n0.addRule(r1, 0, {Symbol.END_SYMBOL})
        n0.addRule(r2, 0, {a, b})
        n0.addRule(r3, 0, {a, b})

        n1 = Node(1)
        n1.addRule(r0, 1, {Symbol.END_SYMBOL})

        n2 = Node(2)
        n2.addRule(r1, 1, {Symbol.END_SYMBOL})
        n2.addRule(r2, 1, {a, b})

        n3 = Node(3)
        n3.addRule(r1, 2, {Symbol.END_SYMBOL})

        n4 = Node(4)
        n4.addRule(r2, 2, {a, b})

        EXP_NODES = [n0, n1, n2, n3, n4]

        self._checkNodes(EXP_NODES, lalr.nodes)

        n0.addTrans(A, n1)
        n0.addTrans(B, n2)

        n2.addTrans(b, n3)
        n2.addTrans(a, n4)

        self._checkTransitions(EXP_NODES, lalr.nodes)
