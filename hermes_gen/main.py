import re
from typing import List, TextIO
from argparse import ArgumentParser
from datetime import datetime
import os

from hermes_gen.grammar import parse_grammar, Grammar
from hermes_gen.lalr1_automata import LALR1Automata, ParseTable, Action
from hermes_gen.consts import ARG_VECTOR
from hermes_gen.errors import HermesError
from hermes_gen.directives import Directive


def main():
    parser = ArgumentParser()
    parser.add_argument("grammar_file")
    parser.add_argument(
        '-s', '--symbol', default="symbol.h", help="Overrides the symbol header filename, defaults to 'symbol.h'"
    )
    parser.add_argument(
        "-t", '--table', default="_parseTable.h", help="Override the table filename, defaults to _parseTable.h"
    )

    args = parser.parse_args()

    grammar_file = args.grammar_file

    if not os.path.exists(grammar_file):
        print("Cannot open grammar file:", grammar_file)
        exit(1)

    try:
        grammar = parse_grammar(grammar_file)
    except Exception as err:
        print("Cannot parse grammar:", err)
        exit(1)

    try:
        lalr = LALR1Automata(grammar)
    except HermesError as err:
        print("Unable to compute LALR(1) Automata:", err)
        exit(1)

    try:
        table = ParseTable(lalr)
    except HermesError as err:
        print("Unable to generate parse table:", err)
        exit(1)

    tableFile = args.table
    symbolFile = args.symbol

    folder, _ = os.path.split(tableFile)
    os.makedirs(folder, exist_ok=True)
    folder, _ = os.path.split(symbolFile)
    os.makedirs(folder, exist_ok=True)

    header = ("/*******\n"
              "This file was generated by Hermes, do not edit\n"
              f"{datetime.now()}\n"
              "*******/\n")

    # Generate token file
    with open(symbolFile, mode='w') as f:
        f.write(header)
        write_symbolFile(f, table, grammar)

    with open(tableFile, mode='w') as f:
        f.write(header)
        f.write(
            "#include <hermes/parseTable.h>\n"
            "#include <hermes/parser.h>\n"
            "#include <hermes/stackItem.h>\n"
            "\n"
            "#include <vector>\n"
            "#include <string>\n"
            "#include <map>\n"
            "\n"
            "#include <boost/regex.hpp>\n"
            "\n"
        )

        try:
            usings = grammar.directives[Directive.using]
            f.write("// Begin user defined using")
            for x in usings:
                f.write(f'using namespace {x}')
            f.write("// End user defined using")
        except KeyError:
            pass

        f.write("namespace hermes\n"
                "{\n"
                "\n")

        f.write("const std::vector<std::string> SYMBOL_LOOKUP = {\n")
        for symbol in table.symbolList:
            f.write(f'   "{symbol}",\n')
        f.write('    "__IGNORE__"\n')
        f.write("}; // End SYMBOL_LOOKUP\n\n")

        f.write("const std::vector<Terminal> TERMINALS = {\n")

        def escape_regex(r: str) -> str:
            regex = re.sub(r"\\", r"\\\\", r)
            regex = re.sub(r'"', r'\\"', regex)
            return regex

        for idx, terminal in enumerate(grammar.terminalList):
            regex = escape_regex(terminal[1])
            f.write(f'    {{Symbol::{terminal[0]}, boost::regex("{regex}")}}')
            if idx < len(grammar.terminalList) - 1:
                f.write(",\n")
        # Write ignored terminals
        if Directive.ignore in grammar.directives:
            for ignore in grammar.directives[Directive.ignore]:
                regex = escape_regex(ignore)
                f.write(f',\n    {{Symbol::__IGNORE__, boost::regex("{regex}")}}')
        f.write("\n}; // End TERMINALS\n\n")

        f.write("const std::vector<Reduction> REDUCTIONS = {\n")

        for idx, rule in enumerate(grammar.rules):
            # Plus 1 to re-offset for the start symbol
            f.write(f'{{{len(rule.symbols)} , {table.symbolIDs[rule.nonterm] + 1}}}')
            if idx < len(grammar.rules) + 1:
                f.write(',')
            f.write('\n')
        f.write("}; // End REDUCTIONS\n\n")

        tableRows = len(table.table)
        tableCols = len(table.table[0])

        f.write(
            f"constexpr unsigned TABLE_ROWS = {tableRows};\n"
            f"constexpr unsigned TABLE_COLS = {tableCols};\n"
            f"const ParseAction PARSE_TABLE[{tableRows}][{tableCols}] = {{\n"
        )

        for rowIdx, row in enumerate(table.table):
            f.write("{ ")
            for idx, action in enumerate(row):
                if action.action != Action.E:
                    f.write(f"{{{action.action}, {action.state}}}")
                else:
                    f.write('{}')
                if idx < len(row) - 1:
                    f.write(", ")

            f.write(" }")  # End Parse Row
            if rowIdx < len(table.table) - 1:
                f.write(",")
            f.write("\n")
        f.write("}; // End parse table\n")

        f.write("using reductionFunc = HERMES_RETURN (*)(std::vector<StackItemPtr>);\n")

        for idx, rule in enumerate(grammar.rules):
            f.write(f"HERMES_RETURN r{idx}(std::vector<StackItemPtr> {ARG_VECTOR})\n"
                    "{\n"
                    f"    {rule.code}\n"
                    "}\n")

        f.write("const std::vector<reductionFunc> reductionFuncs = {\n")
        for idx, rule in enumerate(grammar.rules):
            f.write(f'r{idx}')
            if idx + 1 < len(grammar.rules):
                f.write(',')
            f.write("\n")
        f.write("}; // End reduction func list\n")

        f.write("} // End namespace hermes\n")


def write_symbolFile(f: TextIO, table: ParseTable, grammar: Grammar):
    f.write('#pragma once\n')

    try:
        includes = grammar.directives[Directive.include]
        f.write("// Begin user directed includes\n")
        for inc in includes:
            f.write(f"#include {inc}\n")
        f.write('// End user directed includes\n\n')

    except KeyError:
        pass

    f.write('namespace hermes\n'
            '{\n'
            '\n'
            'enum class Symbol\n'
            '{\n')

    for terminal in table.symbolList:
        f.write(f"    {terminal},\n")
    f.write("    __IGNORE__\n")
    f.write("};\n\n")  # End enum Symbol

    # This is error checked in ebnf_grammer.py
    f.write(f"#define HERMES_RETURN {grammar.directives[Directive.return_][0]}\n\n")

    f.write('} // End namespace hermes\n')


if __name__ == '__main__':
    main()
