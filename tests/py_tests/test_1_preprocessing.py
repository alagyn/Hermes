import unittest
import os.path

import hermes_gen.preprocessing as preprocess

import utils

EXPECTED_CLEAN = [
    r'%return int',
    'semicolon = ";";',
    'open_curly = "{";',
    'close_curly = "}";',
    r'open_paren = "\(";',
    r'close_paren =   "\)";',
    'equals_sign   = "=";',
    'pound = "#";',
    'name = "[a-zA-Z][a-zA-Z0-9_]*";',
    "integer = '[1-9][0-9]*';",
    'PROGRAM   = stmt;',
    'stmt =   name equals_sign integer',
    'semicolon',
    '| open_curly integer   close_curly',
    '{',
    '//this is some code;',
    '//"this is an inner string";',
    'return std::atoi($1);'
    '}',
    "| EMPTY;"
]

EXPECTED_COMBINED = [
    r'%return int',
    'semicolon = ";";',
    'open_curly = "{";',
    'close_curly = "}";',
    r'open_paren = "\(";',
    r'close_paren =   "\)";',
    'equals_sign   = "=";',
    'pound = "#";',
    'name = "[a-zA-Z][a-zA-Z0-9_]*";',
    "integer = '[1-9][0-9]*';",
    'PROGRAM   = stmt;',
    'stmt =   name equals_sign integer semicolon | open_curly integer   close_curly { this is some code; "this is an inner string"; } | EMPTY;'
]


class TestPreprocess(unittest.TestCase):

    def test_preprocess(self):
        testFile = utils.getTestFilename('test.ebnf')

        cleanLines = preprocess.read_and_clean(testFile)

        for exp, act in zip(EXPECTED_CLEAN, cleanLines):
            self.assertEqual(exp, act)

        # Check the length just in case, zip doesn't do this
        self.assertEqual(len(EXPECTED_CLEAN), len(cleanLines), 'The length of the combined lines')

        combined = preprocess.combine_lines(cleanLines)

        for exp, act in zip(EXPECTED_COMBINED, combined):
            self.assertEqual(exp, act)

        self.assertEqual(len(EXPECTED_COMBINED), len(combined), 'The length of the combined lines')