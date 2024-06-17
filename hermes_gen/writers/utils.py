from typing import TextIO
from hermes_gen.grammar import Grammar
from hermes_gen.directives import Directive


def writeUserHeader(f: TextIO, grammar: Grammar):
    try:
        headers = grammar.directives[Directive.header]
        f.write("// Begin user directed headers\n")

        for header in headers:
            f.write("// ----------------------")
            for line in header.splitlines():
                f.write(line.strip())
                f.write("\n")
            f.write("// ----------------------")

        f.write('// End user directed headers\n\n')

    except KeyError:
        pass
