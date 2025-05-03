from argparse import ArgumentParser

import os

from hermes_gen.grammar import parse_grammar
from hermes_gen.lalr1_automata import LALR1Automata, writeDescription
from hermes_gen.parseTable import ParseTable
from hermes_gen.counterexample.counterexampleGen import CounterExampleGen
from hermes_gen.errors import HermesError
from hermes_gen.writers import loader, table, pybind
from hermes_gen import hermes_logs


def main():
    parser = ArgumentParser()
    parser.add_argument("grammar_file")
    parser.add_argument("-n", "--name", help="The grammar name", default="")
    parser.add_argument("-t", '--table', help="The table filename", default="")
    parser.add_argument(
        "-a",
        "--automata",
        default="",
        help="Write a full description of the generated automata to the specified file",
    )
    parser.add_argument("-l", "--loader", help="The loader header filename", default="")
    parser.add_argument("-i", "--impl", help="The loader implementation filename", default="")
    parser.add_argument("-p", "--pybind", help="The pybind loader filename", default="")
    parser.add_argument("--no-examples", help="Disable counterexample generation for conflicts", action="store_true")
    parser.add_argument("-s", "--strict", help="Return an error if an unresolved conflict occurs", action="store_true")
    parser.add_argument("--hide-conflicts", help="Do not print out conflict warnings", action="store_true")
    parser.add_argument("--no-color", help="Disable terminal colors", action="store_true")

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

    tableFile: str = args.table
    loaderHeaderFile: str = args.loader
    loaderImplFile: str = args.impl
    pybindFile: str = args.pybind
    name: str = args.name

    for file in [tableFile, loaderHeaderFile, loaderImplFile]:
        if len(file) > 0:
            folder, _ = os.path.split(file)
            os.makedirs(folder, exist_ok=True)

    if len(tableFile) > 0:
        table.writeParseTable(tableFile, grammar, parseTable)
    if len(loaderImplFile) > 0 or len(loaderHeaderFile) > 0:
        if len(loaderHeaderFile) == 0 or len(loaderImplFile) == 0:
            hermes_logs.err("Please specify both -l and -i")
            exit(1)
        loader.writeLoader(loaderHeaderFile, loaderImplFile, name, grammar)
    if len(pybindFile) > 0:
        pybind.writePybindModule(pybindFile, grammar, name)


if __name__ == '__main__':
    main()
