import unittest

from hermes_gen.__main__ import parse_grammar
from hermes_gen.grammar import Rule, Symbol
from .utils import getTestFilename
from hermes_gen.directives import Directive


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
            "quote": '"',
            "__EOF__": ""
        }

        numTerminals = 0
        for key, val in Symbol._SYMBOL_MAP.items():
            if val.isTerminal:
                numTerminals += 1
                self.assertTrue(key in EXP_TERMS, f'Terminal "{key}" is not expected')
                self.assertEqual(
                    EXP_TERMS[key], val.regex, f'Terminal definition "{key}": "{val.regex}" is not expected'
                )

        self.assertEqual(len(EXP_TERMS), numTerminals, 'Len of terminal definitions not equal')

        program = Symbol.get("PROGRAM")
        stmt = Symbol.get('stmt')
        name = Symbol.get('name')
        equ = Symbol.get('equals_sign')
        integer = Symbol.get('integer')
        semicolon = Symbol.get('semicolon')
        open_curly = Symbol.get('open_curly')
        close_curly = Symbol.get('close_curly')
        x = Symbol.get("x")

        EXP_RULES = [
            Rule(0, program, [stmt], "return values[0]->nt();", "", 0, 0),
            Rule(1, stmt, [name, equ, integer, semicolon], "return 0;", "", 0, 0),
            Rule(
                2,
                stmt, [open_curly, integer, close_curly],
                "#this is a preprocessor thing\n"
                "    //this is some code;\n"
                '    //"this is an inner string";\n'
                "    if(this is an inner block)\n"
                "    {\n"
                "        asdf;\n"
                "    }\n"
                "    std::cout << values[2]->loc.lineStart;\n"
                "    return std::atoi(values[1]->t());",
                "",
                0,
                0
            ),
            Rule(3, stmt, [], "return 0;", "", 0, 0),
            Rule(4, x, [], "return -1;", "", 0, 0),
            Rule(5, stmt, [semicolon], "", "", 0, 0)
        ]

        self.assertEqual(len(EXP_RULES), len(g.rules), 'Len of rules not equal')

        for exp, act in zip(EXP_RULES, g.rules):
            self.assertEqual(exp, act, "Rule definition is not as expected")
            self.assertEqual(exp.code, act.code)

        self.assertTrue(stmt.nullable)
        self.assertTrue(x.nullable)
        self.assertFalse(program.nullable)
        self.assertEqual(g.directives[Directive.return_][0], "int")

    # TODO invalid test files?
