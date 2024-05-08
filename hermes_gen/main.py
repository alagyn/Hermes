import re
from typing import List, TextIO
from argparse import ArgumentParser

import os

from hermes_gen.grammar import parse_grammar, Grammar
from hermes_gen.lalr1_automata import LALR1Automata, ParseTable, writeDescription

from hermes_gen.errors import HermesError
from hermes_gen.directives import Directive

from hermes_gen.writers import loader, parseTable


def main():
    parser = ArgumentParser()
    parser.add_argument("grammar_file")
    parser.add_argument("-n", "--name", help="The grammar name")
    parser.add_argument("-t", '--table', help="The table filename")
    parser.add_argument(
        "-a", "--automata", default="", help="Write a full description of the generated automata to the specified file"
    )
    parser.add_argument("-l", "--loader", help="The loader header filename")
    parser.add_argument("-i", "--impl", help="The loader implementation filename")

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

    if len(args.automata) > 0:
        writeDescription(args.automata, lalr)

    try:
        table = ParseTable(lalr)
    except HermesError as err:
        print("Unable to generate parse table:", err)
        exit(1)

    tableFile: str = args.table
    loaderHeaderFile: str = args.loader
    loaderImplFile: str = args.impl
    name: str = args.name

    folder, _ = os.path.split(tableFile)
    os.makedirs(folder, exist_ok=True)
    folder, _ = os.path.split(loaderHeaderFile)
    os.makedirs(folder, exist_ok=True)

    parseTable.writeParseTable(tableFile, grammar_file, grammar, table)
    loader.writeLoader(loaderHeaderFile, loaderImplFile, tableFile, name, grammar)


if __name__ == '__main__':
    main()
