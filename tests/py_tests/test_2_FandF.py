import unittest
from typing import Dict, Set

from . import utils
from hermes_gen.grammar import parse_grammar, Symbol
from hermes_gen.consts import EMPTY, END, START


def _convert(d: Dict[str, Set[str]]) -> Dict[Symbol, Set[Symbol]]:
    out = {}
    for k, v in d.items():
        kSym = Symbol.get(k)
        vSet = set()
        for s in v:
            vSet.add(Symbol.get(s))

        out[kSym] = vSet

    return out


class TestFirstAndFollow(unittest.TestCase):

    def _check(self, expectedFirstStr: Dict[str, Set[str]], expectedFollowStr: Dict[str, Set[str]]):

        expectedFirst = _convert(expectedFirstStr)
        expectedFollow = _convert(expectedFollowStr)

        seenFirst = 0
        seenFollow = 0

        for val in Symbol._SYMBOL_MAP.values():
            if val in {Symbol.EMPTY_SYMBOL, Symbol.END_SYMBOL, Symbol.START_SYMBOL}:
                continue

            self.assertTrue(val in expectedFirst, f'{val} not in expected FIRST dict')

            expFirst = expectedFirst[val]
            diff = expFirst ^ val.first
            self.assertEqual(0, len(diff), f'Bad FIRST set for {val}\n\texp: {expFirst}\n\tgot: {val.first}')
            seenFirst += 1

            if not val.isTerminal:
                self.assertTrue(val in expectedFollow, f'{val} not in expected FOLLOW dict')

                expFollow = expectedFollow[val]
                diff = expFollow ^ val.follow
                self.assertEqual(0, len(diff), f'Bad FOLLOW set for {val}\n\texp: {expFollow}\n\tgot: {val.follow}')

                seenFollow += 1

        # TODO log missing stuff
        self.assertEqual(len(expectedFirst), seenFirst, "Missing symbols from FIRST set")
        self.assertEqual(len(expectedFollow), seenFollow, "Missing symbols from FOLLOW set")

    def test_1(self):
        """
        From compiler book by Thain
        """
        testFile = utils.getTestFilename("FandFtest1.hm")
        grammar = parse_grammar(testFile)

        EXP_FIRST = {
            'P': {'open_p', 'int'},
            'E': {'open_p', 'int'},
            'EP': {'plus', EMPTY},
            'T': {'open_p', 'int'},
            'TP': {'star', EMPTY},
            'F': {'open_p', 'int'},
            'plus': {'plus'},
            'star': {'star'},
            'open_p': {'open_p'},
            'close_p': {'close_p'},
            'int': {'int'}
        }

        EXP_FOLLOW = {
            'P': {END},
            'E': {'close_p', END},
            'EP': {'close_p', END},
            'T': {'close_p', 'plus', END},
            'TP': {'plus', 'close_p', END},
            'F': {'plus', 'star', 'close_p', END}
        }

        self._check(EXP_FIRST, EXP_FOLLOW)

    def test_2(self):
        """
        Test from https://people.cs.pitt.edu/~jmisurda/teaching/cs1622/handouts/cs1622-first_and_follow.pdf
        """
        testFile = utils.getTestFilename('FandFtest2.hm')
        g = parse_grammar(testFile)

        EXP_FIRST = {
            'Y': {'star', EMPTY},
            'X': {'plus', EMPTY},
            'T': {'open_p', 'int'},
            'E': {'open_p', 'int'},
            'plus': {'plus'},
            'star': {'star'},
            'open_p': {'open_p'},
            'close_p': {'close_p'},
            'int': {'int'}
        }

        EXP_FOLLOW = {
            'Y': {'close_p', END, 'plus'},
            'X': {'close_p', END},
            'T': {'close_p', END, 'plus'},
            'E': {'close_p', END}
        }

        self._check(EXP_FIRST, EXP_FOLLOW)

    def test_3_G10(self):
        """
        Grammar G10 from Thain book
        """
        testFile = utils.getTestFilename('G10.hm')
        g = parse_grammar(testFile)

        EXP_FIRST = {
            "id": {"id"},
            "plus": {"plus"},
            "open_p": {"open_p"},
            "close_p": {"close_p"},
            'P': {"id"},
            'E': {"id"},
            "T": {"id"}
        }

        EXP_FOLLOW = {
            "P": {END},
            "E": {"plus", END, "close_p"},
            "T": {"close_p", "plus", END}
        }

        self._check(EXP_FIRST, EXP_FOLLOW)

    def test_4_epsilon(self):
        testFile = utils.getTestFilename('epsilon.hm')
        g = parse_grammar(testFile)

        # yapf: disable
        EXP_FIRST = {
            "a": {"a"},
            "b": {"b"},
            "S": {"b", "a", EMPTY},
            "A": {"b", "a", EMPTY},
            "B": {"a", EMPTY}
        }

        EXP_FOLLOW = {
            "S": {END},
            "A": {END},
            "B": {'b', 'a'}
        }
        # yapf: enable

        self._check(EXP_FIRST, EXP_FOLLOW)
