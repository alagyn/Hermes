import unittest
from typing import List

from . import utils

from hermes_gen.lalr1_automata import Node, AnnotRule, LALR1Automata
from hermes_gen.grammar import Grammar, Rule, parse_grammar, Symbol
from hermes_gen.consts import END


def rule(id: int, nonterm: Symbol, symbols: List[Symbol]) -> Rule:
    return Rule(id, nonterm, symbols, "", "", 0, 0)


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

        r0 = rule(1, SP, [S])
        r1 = rule(2, S, [X, X])
        r2 = rule(3, X, [a, X])

        n0 = Node(0)
        n0.addRule(r0, 0, {Symbol.END})
        n0.addRule(r1, 1, {Symbol.END})
        n0.addRule(r2, 0, {a, Symbol.END})

        n1 = Node(1)
        n1.addRule(r0, 0, {a, Symbol.END})
        n1.addRule(r1, 1, {b})
        n1.addRule(r2, 0, {a, b})

        n0.combine(n1)

        expNode = Node(2)
        expNode.addRule(r0, 0, {a, Symbol.END})
        expNode.addRule(r1, 1, {b, Symbol.END})
        expNode.addRule(r2, 0, {a, b, Symbol.END})

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

        r0 = rule(1, SP, [S])
        r1 = rule(2, S, [X, X])
        r2 = rule(3, X, [a, X])
        r3 = rule(4, X, [b])

        n0 = Node(0)
        n0.addRule(r0, 0, {Symbol.END})
        n0.addRule(r1, 0, {Symbol.END})
        n0.addRule(r2, 0, {a, b})
        n0.addRule(r3, 0, {a, b})

        n1 = Node(1)
        n1.addRule(r0, 1, {Symbol.END})

        n2 = Node(2)
        n2.addRule(r1, 1, {Symbol.END})
        n2.addRule(r2, 0, {Symbol.END})
        n2.addRule(r3, 0, {Symbol.END})

        n36 = Node(3)
        n36.addRule(r2, 1, {a, b, Symbol.END})
        n36.addRule(r2, 0, {a, b, Symbol.END})
        n36.addRule(r3, 0, {a, b, Symbol.END})

        n5 = Node(4)
        n5.addRule(r1, 2, {Symbol.END})

        n47 = Node(5)
        n47.addRule(r3, 1, {a, b, Symbol.END})

        n89 = Node(6)
        n89.addRule(r2, 2, {a, b, Symbol.END})

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

        r1 = Rule(1, P, [E], "", "", 0, 0)
        r2 = Rule(2, E, [E, plus, T], "", "", 0, 0)
        r3 = Rule(3, E, [T], "", "", 0, 0)
        r4 = Rule(4, T, [_id, open_p, E, close_p], "", "", 0, 0)
        r5 = Rule(5, T, [_id], "", "", 0, 0)

        n0 = Node(0)
        n0.addRule(r1, 0, {Symbol.END})
        n0.addRule(r2, 0, {plus, Symbol.END})
        n0.addRule(r3, 0, {plus, Symbol.END})
        n0.addRule(r4, 0, {plus, Symbol.END})
        n0.addRule(r5, 0, {plus, Symbol.END})

        n1 = Node(1)
        n1.addRule(r1, 1, {Symbol.END})
        n1.addRule(r2, 1, {plus, Symbol.END})

        n2 = Node(2)
        n2.addRule(r3, 1, {plus, close_p, Symbol.END})

        n3 = Node(3)
        n3.addRule(r4, 1, {plus, close_p, Symbol.END})
        n3.addRule(r5, 1, {plus, close_p, Symbol.END})

        n4 = Node(4)
        n4.addRule(r2, 2, {plus, close_p, Symbol.END})
        n4.addRule(r4, 0, {plus, close_p, Symbol.END})
        n4.addRule(r5, 0, {plus, close_p, Symbol.END})

        n5 = Node(5)
        n5.addRule(r4, 2, {plus, close_p, Symbol.END})
        n5.addRule(r2, 0, {plus, close_p})
        n5.addRule(r3, 0, {plus, close_p})
        n5.addRule(r4, 0, {plus, close_p})
        n5.addRule(r5, 0, {plus, close_p})

        n6 = Node(6)
        n6.addRule(r2, 3, {plus, close_p, Symbol.END})

        n7 = Node(7)
        n7.addRule(r4, 3, {plus, close_p, Symbol.END})
        n7.addRule(r2, 1, {plus, close_p})

        n8 = Node(8)
        n8.addRule(r4, 4, {plus, close_p, Symbol.END})

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

        r0 = rule(0, S, [A])
        r1 = rule(1, A, [B, b])
        r2 = rule(2, B, [B, a])
        r3 = rule(3, B, [])

        n0 = Node(0)
        n0.addRule(r0, 0, {Symbol.END})
        n0.addRule(r1, 0, {Symbol.END})
        n0.addRule(r2, 0, {a, b})
        n0.addRule(r3, 0, {a, b})

        n1 = Node(1)
        n1.addRule(r0, 1, {Symbol.END})

        n2 = Node(2)
        n2.addRule(r1, 1, {Symbol.END})
        n2.addRule(r2, 1, {a, b})

        n3 = Node(3)
        n3.addRule(r1, 2, {Symbol.END})

        n4 = Node(4)
        n4.addRule(r2, 2, {a, b})

        EXP_NODES = [n0, n1, n2, n3, n4]

        self._checkNodes(EXP_NODES, lalr.nodes)

        n0.addTrans(A, n1)
        n0.addTrans(B, n2)

        n2.addTrans(b, n3)
        n2.addTrans(a, n4)

        self._checkTransitions(EXP_NODES, lalr.nodes)

    def test_4_unambiguous_SR(self):
        testFile = utils.getTestFilename("conflicts/unambiguous-shift-reduce.hm")
        g = parse_grammar(testFile)
        lalr = LALR1Automata(g)

        START = Symbol.get("__START__")
        S = Symbol.get("S")
        T = Symbol.get("T")
        X = Symbol.get("X")
        Y = Symbol.get("Y")
        a = Symbol.get("a")
        b = Symbol.get("b")
        EOF = Symbol.get("__EOF__")

        r0 = rule(0, START, [S, EOF])
        r1 = rule(1, S, [T])
        r2 = rule(2, S, [S, T])
        r3 = rule(3, T, [X])
        r4 = rule(4, T, [Y])
        r5 = rule(5, X, [a])
        r6 = rule(6, Y, [a, a, b])

        la = {Symbol.END, a}

        n0 = Node(0)
        n0.addRule(r0, 0, {Symbol.END})
        n0.addRule(r1, 0, la)
        n0.addRule(r2, 0, la)
        n0.addRule(r3, 0, la)
        n0.addRule(r4, 0, la)
        n0.addRule(r5, 0, la)
        n0.addRule(r6, 0, la)

        n1 = Node(1)
        n1.addRule(r0, 1, {Symbol.END})
        n1.addRule(r2, 1, la)
        n1.addRule(r3, 0, la)
        n1.addRule(r4, 0, la)
        n1.addRule(r5, 0, la)
        n1.addRule(r6, 0, la)

        n2 = Node(2)
        n2.addRule(r1, 1, la)

        n3 = Node(3)
        n3.addRule(r3, 1, la)

        n4 = Node(4)
        n4.addRule(r4, 1, la)

        n5 = Node(5)
        n5.addRule(r5, 1, la)
        n5.addRule(r6, 1, la)

        n6 = Node(6)
        n6.addRule(r0, 2, {Symbol.END})

        n7 = Node(7)
        n7.addRule(r2, 2, la)

        n8 = Node(8)
        n8.addRule(r6, 2, la)

        n9 = Node(9)
        n9.addRule(r6, 3, la)

        EXP_NODES = [n0, n1, n2, n3, n4, n5, n6, n7, n8, n9]

        self._checkNodes(EXP_NODES, lalr.nodes)

        n0.addTrans(S, n1)
        n0.addTrans(T, n2)
        n0.addTrans(X, n3)
        n0.addTrans(Y, n4)
        n0.addTrans(a, n5)

        n1.addTrans(X, n3)
        n1.addTrans(Y, n4)
        n1.addTrans(a, n5)
        n1.addTrans(EOF, n6)
        n1.addTrans(T, n7)

        n5.addTrans(a, n8)

        n8.addTrans(b, n9)

        self._checkTransitions(EXP_NODES, lalr.nodes)

    def test_5_epsilon2(self):
        testFile = utils.getTestFilename("epsilon2.hm")
        g = parse_grammar(testFile)
        lalr = LALR1Automata(g)

        A = Symbol.get("A")
        IF = Symbol.get("IF")
        ELSE = Symbol.get("ELSE")

        s = Symbol.get("s")
        ifs = Symbol.get("ifs")
        if_ = Symbol.get("if_")
        else_ = Symbol.get("else_")

        r0 = rule(0, s, [ifs])
        r1 = rule(1, ifs, [if_, ifs])
        r2 = rule(2, ifs, [if_])
        r3 = rule(3, if_, [IF, A, else_])
        r4 = rule(4, else_, [ELSE, A])
        r5 = rule(5, else_, [])

        laEnd = {Symbol.END}
        laIF = {Symbol.END, IF}

        n0 = Node(0)
        n0.addRule(r0, 0, laEnd)
        n0.addRule(r1, 0, laEnd)
        n0.addRule(r2, 0, laEnd)
        n0.addRule(r3, 0, laIF)

        n1 = Node(1)
        n1.addRule(r0, 1, laEnd)

        n2 = Node(2)
        n2.addRule(r1, 1, laEnd)
        n2.addRule(r2, 1, laEnd)
        n2.addRule(r1, 0, laEnd)
        n2.addRule(r2, 0, laEnd)
        n2.addRule(r3, 0, laIF)

        n3 = Node(3)
        n3.addRule(r3, 1, laIF)

        n4 = Node(4)
        n4.addRule(r1, 2, laEnd)

        n5 = Node(5)
        n5.addRule(r3, 2, laIF)
        n5.addRule(r4, 0, laIF)
        n5.addRule(r5, 0, laIF)

        n6 = Node(6)
        n6.addRule(r3, 3, laIF)

        n7 = Node(7)
        n7.addRule(r4, 1, laIF)

        n8 = Node(8)
        n8.addRule(r4, 2, laIF)

        EXP_NODES = [n0, n1, n2, n3, n4, n5, n6, n7, n8]

        self._checkNodes(EXP_NODES, lalr.nodes)

        n0.addTrans(ifs, n1)
        n0.addTrans(if_, n2)
        n0.addTrans(IF, n3)

        n2.addTrans(ifs, n4)
        n2.addTrans(if_, n2)
        n2.addTrans(IF, n3)

        n3.addTrans(A, n5)

        n5.addTrans(else_, n6)
        n5.addTrans(ELSE, n7)

        n7.addTrans(A, n8)

        self._checkTransitions(EXP_NODES, lalr.nodes)
