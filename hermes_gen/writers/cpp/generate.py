from argparse import ArgumentParser
import os

from hermes_gen import hermes_logs
from hermes_gen.grammar import Grammar
from hermes_gen.parseTable import ParseTable
from . import loader, table


def getArguments(parser: ArgumentParser):
    parser.add_argument("-l", "--loader", help="The loader header filename", default="")
    parser.add_argument("-i", "--impl", help="The loader implementation filename", default="")
    parser.add_argument("-t", '--table', help="The table filename", default="")


def generate(grammar: Grammar, parseTable: ParseTable, args):
    tableFile: str = args.table
    loaderHeaderFile: str = args.loader
    loaderImplFile: str = args.impl
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
        loader.writeLoader(loaderHeaderFile, loaderImplFile, tableFile, name, grammar)
