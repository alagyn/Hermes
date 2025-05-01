import re
from typing import List, TextIO
from argparse import ArgumentParser

import os
import sys

from hermes_gen.grammar import parse_grammar
from hermes_gen.lalr1_automata import LALR1Automata, writeDescription
from hermes_gen.parseTable import ParseTable
from hermes_gen.counterexample.counterexampleGen import CounterExampleGen
from hermes_gen.errors import HermesError
from hermes_gen.directives import Directive
import hermes_gen.writers.cpp.generate as cppGen
from hermes_gen import hermes_logs


def main():
    parser = ArgumentParser()
    parser.add_argument("grammar_file")
    parser.add_argument("-n", "--name", help="The grammar name", default="")
    parser.add_argument(
        "-a",
        "--automata",
        default="",
        help="Write a full description of the generated automata to the specified file",
    )
    parser.add_argument("--no-examples", help="Disable counterexample generation for conflicts", action="store_true")
    parser.add_argument("-s", "--strict", help="Return an error if an unresolved conflict occurs", action="store_true")
    parser.add_argument("--hide-conflicts", help="Do not print out conflict warnings", action="store_true")
    parser.add_argument("--no-color", help="Disable terminal colors", action="store_true")

    subparsers = parser.add_subparsers(help="Generate modes")
    cppArgs = subparsers.add_parser("cpp")
    pyArgs = subparsers.add_parser("python")

    cppGen.getArguments(cppArgs)

    args = parser.parse_args()

    grammar_file: str = args.grammar_file
    genExamples: bool = not args.no_examples
    strict: bool = args.strict
    hideConflicts: bool = args.hide_conflicts

    colors: bool = not args.no_color

    hermes_logs.enableColors(colors)

    if not os.path.exists(grammar_file):
        hermes_logs.err("Cannot open grammar file:", grammar_file)
        exit(1)

    try:
        grammar = parse_grammar(grammar_file)
    except HermesError as err:
        hermes_logs.err("Cannot parse grammar:", str(err))
        exit(1)

    try:
        lalr = LALR1Automata(grammar)
    except HermesError as err:
        hermes_logs.err("Unable to compute LALR(1) Automata:", str(err))
        exit(1)

    if len(args.automata) > 0:
        writeDescription(args.automata, lalr)

    try:
        parseTable = ParseTable(lalr)
    except HermesError as err:
        hermes_logs.err("Unable to generate parse table:", str(err))
        exit(1)

    if len(parseTable.conflicts) > 0:
        if not hideConflicts:
            if genExamples:
                ceGen = CounterExampleGen(lalr)
                for conflict in parseTable.conflicts:
                    ce = ceGen.generate_counterexample(conflict)
                    msg = ce.prettyPrint(colors)
                    if strict:
                        hermes_logs.err(f'Conflict detected in {conflict.node}')
                    else:
                        hermes_logs.warn(f'Conflict detected in {conflict.node}')

                    hermes_logs.info(msg + "\n")
            else:
                for conflict in parseTable.conflicts:
                    if strict:
                        hermes_logs.err(str(conflict) + "\n")
                    else:
                        hermes_logs.warn(str(conflict) + "\n")

        if strict:
            hermes_logs.err("Strict mode enabled and conflicts found, refusing to generate parser")
            exit(2)


if __name__ == '__main__':
    main()
