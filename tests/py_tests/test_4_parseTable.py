import unittest

from . import utils
from hermes_gen.grammar import Grammar, parse_grammar, Symbol
from hermes_gen.lalr1_automata import LALR1Automata
from hermes_gen.parseTable import ParseTable, Action, TableType, ParseAction


def G(x: int) -> ParseAction:
    return ParseAction(Action.G, x)


E = ParseAction(Action.E, 0)


def S(x: int) -> ParseAction:
    return ParseAction(Action.S, x)


def R(x: int) -> ParseAction:
    return ParseAction(Action.R, x)


class TestParseTable(unittest.TestCase):

    def _checkTable(self, exp: TableType, act: TableType):
        for rowIdx, (expRow, actRow) in enumerate(zip(exp, act)):
            for colIdx, (expCol, actCol) in enumerate(zip(expRow, actRow)):
                self.assertEqual(expCol, actCol, f"Error at [{rowIdx}][{colIdx}] expected {expCol} got {actCol}")

            self.assertEqual(len(expRow), len(actRow), f"Row {rowIdx} not of equal length")
        self.assertEqual(len(exp), len(act), f"Table not of equal size")

    def test_1_G10(self):
        testFile = utils.getTestFilename("G10.hm")
        grammar = parse_grammar(testFile)
        lalr = LALR1Automata(grammar)
        table = ParseTable(lalr)

        symbols = [
            Symbol.get("P"),
            Symbol.get("E"),
            Symbol.get("T"),
            Symbol.get("id"),
            Symbol.get("plus"),
            Symbol.get("open_p"),
            Symbol.get("close_p"),
            Symbol.END_SYMBOL
        ]

        for x, y in zip(symbols, table.symbolList):
            self.assertEqual(x, y, f"Symbols out of order, exp: {x} got: {y}")

        self.assertEqual(
            len(symbols),
            len(table.symbolList),
            f"Symbol list not correct\n\tExp: {symbols}\n\tAct: {table.symbolList}"
        )

        # yapf: disable
        EXP_TABLE: TableType = [
            #  E     T     id    +     (     )     $
            #-----------------------------------------
            [G(1), G(2), S(3), E   , E   , E   , E   ],
            [E   , E   , E   , S(4), E   , E   , R(0)],
            [E   , E   , E   , R(2), E   , R(2), R(2)],
            [E   , E   , E   , R(4), S(5), R(4), R(4)],
            [E   , G(6), S(3), E   , E   , E   , E   ],
            [G(7), G(2), S(3), E   , E   , E   , E   ],
            [E   , E   , E   , R(1), E   , R(1), R(1)],
            [E   , E   , E   , S(4), E   , S(8), E   ],
            [E   , E   , E   , R(3), E   , R(3), R(3)]
        ]
        # yapf: enable

        self._checkTable(EXP_TABLE, table.table)

    def test_2_epsilon(self):
        testFile = utils.getTestFilename("epsilon.hm")
        grammar = parse_grammar(testFile)
        lalr = LALR1Automata(grammar)
        table = ParseTable(lalr)

        # yapf: disable
        EXP_TABLE: TableType = [
            #  A     B     b     a     $
            #-----------------------------
            [G(1), G(2), R(3), R(3), E   ],
            [E   , E   , E   , E   , R(0)],
            [E   , E   , S(3), S(4), E   ],
            [E   , E   , E   , E   , R(1)],
            [E   , E   , R(2), R(2), E   ]
        ]
        # yapf: enable

        self._checkTable(EXP_TABLE, table.table)
