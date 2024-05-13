import unittest

from hermes_gen.main import parse_grammar
from hermes_gen.grammar import Rule
from .utils import getTestFilename


class TestBuildgrammar(unittest.TestCase):

    def test_buildgrammar1(self):
        testFile = getTestFilename('test.hm')

        g = parse_grammar(testFile)

        EXP_TERMS = {
            'semicolon': ';',
            'open_curly': "{",
            'close_curly': "}",
            'open_paren': r"\(",
            'close_paren': r"\)",
            'equals_sign': "=",
            'pound': "#",
            'name': "[a-zA-Z][a-zA-Z0-9_]*",
            'integer': '[1-9][0-9]*',
            "quote": '"'
        }

        self.assertEqual(len(EXP_TERMS), len(g.terminals), 'Len of terminal definitions not equal')

        for key, val in g.terminals.items():
            self.assertTrue(key in EXP_TERMS, 'Terminal name is not expected')
            self.assertEqual(EXP_TERMS[key], val, 'Terminal definition is not expected')

        EXP_RULES = [
            Rule(0, 'PROGRAM', ['stmt'], "return values[0]->nt();", 0, 0),
            Rule(1, 'stmt', ['name', 'equals_sign', 'integer', 'semicolon'], "return 0;", 0, 0),
            Rule(
                2,
                'stmt', ['open_curly', 'integer', 'close_curly'],
                "#this is a preprocessor thing\n"
                "    //this is some code;\n"
                '    //"this is an inner string";\n'
                "    if(this is an inner block)\n"
                "    {\n"
                "        asdf;\n"
                "    }\n"
                "    return std::atoi(values[1]->t());",
                0,
                0
            ),
            Rule(3, "stmt", [], "return 0;", 0, 0)
        ]

        self.assertEqual(len(EXP_RULES), len(g.rules), 'Len of rules not equal')

        for exp, act in zip(EXP_RULES, g.rules):
            self.assertEqual(exp, act, "Rule definition is not as expected")
            self.assertEqual(exp.code, act.code)

        # TODO check nulls

    # TODO invalid test files?
