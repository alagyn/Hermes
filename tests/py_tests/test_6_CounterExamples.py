import unittest

from . import utils

from hermes_gen.grammar import parse_grammar, Symbol
from hermes_gen.lalr1_automata import LALR1Automata
from hermes_gen.parseTable import ParseTable
from hermes_gen.counterexample.counterexampleGen import CounterExampleGen
from hermes_gen.counterexample.derivation import Derivation, DOT

D = Derivation


class TestCounterExample(unittest.TestCase):

    def _checkDeriv(self, exp: Derivation, actual: Derivation):
        self.assertEqual(exp, actual)
        self.assertEqual(exp.deriv, actual.deriv)
        if exp.deriv is not None and actual.deriv is not None:
            for x, y in zip(exp.deriv, actual.deriv):
                self._checkDeriv(x, y)

    def test_0_Unamb_SR(self):
        # polyglot: unamb-sr.cup
        testFile = utils.getTestFilename("conflicts/unambiguous-shift-reduce.hm")
        grammar = parse_grammar(testFile)
        lalr = LALR1Automata(grammar)
        table = ParseTable(lalr)

        self.assertEqual(1, len(table.conflicts), "Number of conflicts")

        START = Symbol.get("__START__")
        S = Symbol.get("S")
        T = Symbol.get("T")
        X = Symbol.get("X")
        Y = Symbol.get("Y")
        a = Symbol.get("a")
        b = Symbol.get("b")

        conflict = table.conflicts[0]

        self.assertEqual(a, conflict.symbol)
        self.assertEqual(lalr.nodes[5], conflict.node)
        self.assertTrue(conflict.isShiftReduce)

        gen = CounterExampleGen(lalr)

        ce = gen.generate_counterexample(conflict)

        self.assertFalse(ce.unifying)

        # yapf: disable

        # From java_cup
        # Example using reduction   : a • a EOF
        # Derivation using reduction: $START ::= [S ::= [S ::= [T ::= [X ::= [a •]]] T ::= [X ::= [a]]] EOF]
        # Example using shift       : a • a b EOF
        # Derivation using shift    : $START ::= [S ::= [T ::= [Y ::= [a • a b]]] EOF]

        EXP_DERIV1 = (
        D(START, [
            D(S, [
                D(S, [
                    D(T, [
                        D(X, [
                            D(a), DOT
                        ])
                    ])
                ]),
                D(T, [
                    D(X, [
                        D(a)
                    ])
                ]),
            ])]
            )
        )

        EXP_DERIV2 = (
        D(START, [
            D(S, [
                D(T, [
                    D(Y, [
                        D(a), DOT, D(a), D(b)
                    ])
                ])
            ])
        ])
        )

        # yapf: enable

        self._checkDeriv(EXP_DERIV1, ce.d1)
        self._checkDeriv(EXP_DERIV2, ce.d2)

        self.assertEqual("a • a", ce.prettyExample1())
        self.assertEqual("a • a b", ce.prettyExample2())

    def test_1_Amb_SR(self):
        # polyglot: paper-ex.cup
        testFile = utils.getTestFilename("conflicts/ambiguous-shift-reduce.hm")
        grammar = parse_grammar(testFile)
        lalr = LALR1Automata(grammar)
        table = ParseTable(lalr)

        self.assertEqual(3, len(table.conflicts), "Number of conflicts")

        IF = Symbol.get("IF")
        THEN = Symbol.get("THEN")
        ELSE = Symbol.get("ELSE")
        COLON = Symbol.get("COLON")
        LBRACKET = Symbol.get("LBRACKET")
        RBRACKET = Symbol.get("RBRACKET")
        ASSIGN = Symbol.get("ASSIGN")
        PLUS = Symbol.get("PLUS")
        DIGIT = Symbol.get("DIGIT")
        ARR = Symbol.get("ARR")

        stmt = Symbol.get("stmt")
        expr = Symbol.get("expr")
        num = Symbol.get("num")

        gen = CounterExampleGen(lalr)
        ce0 = gen.generate_counterexample(table.conflicts[0])

        self.assertTrue(ce0.unifying)
        self.assertTrue(stmt, ce0.nonTerminal())

        # yapf: disable

        """
        Warning : *** Shift/Reduce conflict found in state #5
        between reduction on expr ::= num •
        and shift on         num ::= num • DIGIT
        under symbol DIGIT
        Ambiguity detected for nonterminal stmt
        Example: expr COLON ARR LBRACK expr RBRACK ASSIGN num • DIGIT DIGIT COLON stmt stmt
        Derivation using reduction: stmt ::= [expr COLON stmt ::= [ARR LBRACK expr RBRACK ASSIGN expr ::= [num •]] stmt ::= [expr ::= [num ::= [num ::= [DIGIT] DIGIT]] COLON stmt stmt]]
        Derivation using shift    : stmt ::= [expr COLON stmt ::= [ARR LBRACK expr RBRACK ASSIGN expr ::= [num ::= [num • DIGIT]]] stmt ::= [expr ::= [num ::= [DIGIT]] COLON stmt stmt]]
        """

        EXP_DERIV0_1 = (
            D(stmt, [
                D(expr), D(COLON), D(stmt, [
                    D(ARR), D(LBRACKET), D(expr), D(RBRACKET), D(ASSIGN), D(expr, [
                        D(num), DOT
                    ])
                ]),
                D(stmt, [
                    D(expr, [
                        D(num, [
                            D(num, [
                                D(DIGIT)
                            ]),
                            D(DIGIT)
                        ])
                    ]),
                    D(COLON), D(stmt), D(stmt)
                ])
            ])
        )

        EXP_DERIV0_2 = (
            D(stmt, [
                D(expr), D(COLON), D(stmt, [
                    D(ARR), D(LBRACKET), D(expr), D(RBRACKET), D(ASSIGN), D(expr, [
                        D(num, [
                            D(num), DOT, D(DIGIT)
                        ])
                    ])
                ]),
                D(stmt, [
                    D(expr, [
                        D(num, [
                            D(DIGIT)
                        ])
                    ]),
                    D(COLON), D(stmt), D(stmt)
                ])
            ])
        )

        # yapf: enable

        self._checkDeriv(EXP_DERIV0_1, ce0.d1)
        #self._checkDeriv(EXP_DERIV0_2, ce0.d2)

        self.assertEqual(
            "expr COLON ARR LBRACKET expr RBRACKET ASSIGN num • DIGIT DIGIT COLON stmt stmt", ce0.prettyExample1()
        )
