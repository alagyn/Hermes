import re

from hermes_gen.writers.hermesHeader import writeHermesHeader
from hermes_gen.grammar import Grammar
from hermes_gen.directives import Directive
from hermes_gen.lalr1_automata import ParseTable, Action
from hermes_gen.consts import ARG_VECTOR


# FIXME
def writeParseTable(filename: str, grammarFile: str, grammar: Grammar, table: ParseTable):
    with open(filename, mode='w') as f:
        writeHermesHeader(f)

        f.write(
            "#include <hermes/internal/grammar.h>\n"
            "#include <hermes/internal/regex/regex.h>\n"
            "\n"
            "#include <vector>\n"
            "#include <string>\n"
            "#include <map>\n"
            "\n"
        )

        try:
            includes = grammar.directives[Directive.include]
            f.write("// Begin user directed includes\n")
            for inc in includes:
                f.write(f"#include {inc}\n")
            f.write('// End user directed includes\n\n')

        except KeyError:
            pass

        try:
            usings = grammar.directives[Directive.using]
            f.write("// Begin user defined 'using'\n")
            for x in usings:
                f.write(f'using namespace {x};\n')
            f.write("// End user defined 'using'\n")
        except KeyError:
            pass

        f.write("namespace hermes\n"
                "{\n"
                "\n")

        returnType = grammar.directives[Directive.return_][0]

        f.write(
            f"using StackItemPtr = std::shared_ptr<StackItem<{returnType}>>;\n"
            f"using ReductionFunc = {returnType} (*)(std::vector<StackItemPtr>);\n\n"
        )

        f.write("namespace Symbol {\n")
        for idx, terminal in enumerate(table.symbolList):
            f.write(f"unsigned {terminal} = {idx};\n")
        f.write(f"unsigned __IGNORE__ = {len(table.symbolList)};\n")
        f.write("} // end namespace Symbol\n\n")

        f.write("const std::vector<std::string> SYMBOL_LOOKUP = {\n")
        for symbol in table.symbolList:
            f.write(f'   "{symbol}",\n')
        f.write('    "__IGNORE__"\n')
        f.write("}; // End SYMBOL_LOOKUP\n\n")

        f.write("const std::vector<TerminalDef> TERMINALS = {\n")

        def escape_regex(r: str) -> str:
            regex = re.sub(r"\\", r"\\\\", r)
            regex = re.sub(r'"', r'\\"', regex)
            return regex

        for idx, terminal in enumerate(grammar.terminalList):
            regex = escape_regex(terminal[1])
            f.write(f'    {{Symbol::{terminal[0]}, "{regex}"}}')
            if idx < len(grammar.terminalList) - 1:
                f.write(",\n")
        # Write ignored terminals
        if Directive.ignore in grammar.directives:
            for ignore in grammar.directives[Directive.ignore]:
                regex = escape_regex(ignore)
                f.write(f',\n    {{Symbol::__IGNORE__, "{regex}"}}')
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

        f.write(f"using ReductionFunc = {returnType} (*)(std::vector<StackItemPtr>);\n")

        for idx, rule in enumerate(grammar.rules):
            f.write(
                f"{returnType} r{idx}(std::vector<StackItemPtr> {ARG_VECTOR})\n"
                "{\n"
                f'#line {rule.codeLine} "{grammarFile}"\n'
                f"    {rule.code}\n"
                "}\n"
            )

        f.write("const std::vector<ReductionFunc> REDUCTION_FUNCS = {\n")
        for idx, rule in enumerate(grammar.rules):
            f.write(f'r{idx}')
            if idx + 1 < len(grammar.rules):
                f.write(',')
            f.write("\n")
        f.write("}; // End reduction func list\n")

        f.write("} // End namespace hermes\n")
