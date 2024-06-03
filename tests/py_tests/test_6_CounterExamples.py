import unittest

from . import utils

from hermes_gen.grammar import parse_grammar, Symbol
from hermes_gen.lalr1_automata import LALR1Automata
from hermes_gen.parseTable import ParseTable, Conflict


class TestCounterExample(unittest.TestCase):

    def test_0_UA_SR(self):
        # polyglot: unamb-sr.cup
        testFile = utils.getTestFilename("conflicts/unambiguous-shift-reduce.hm")
        grammar = parse_grammar(testFile)
        lalr = LALR1Automata(grammar)
        table = ParseTable(lalr)

        self.assertEqual(1, len(table.conflicts), "Number of conflicts")
