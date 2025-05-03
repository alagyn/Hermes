import re

from hermes_gen.writers.cpp.hermesHeader import writeHermesHeader
from hermes_gen.grammar import Grammar
from hermes_gen.directives import Directive
from hermes_gen.parseTable import ParseTable, Action
from .utils import writeUserHeader
from hermes_gen.code_preproc import CodePreprocessor

ARG_VECTOR = "values"


class CPPPreproc(CodePreprocessor):

    def _get(self, func: str, sIdx: int) -> str:
        return f'{ARG_VECTOR}[{sIdx}]->{func}'

    def _getTerminal(self, sIdx: int) -> str:
        return self._get("t()", sIdx)

    def _getNonterminal(self, sIdx: int) -> str:
        return self._get("nt()", sIdx)

    def _getLoc(self, sIdx: int) -> str:
        return self._get("loc", sIdx)


# TODO change parse table to a list of lists, since most columns are empty


def writeParseTable(filename: str, grammar: Grammar, table: ParseTable):
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

        writeUserHeader(f, grammar)

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
            f.write(f"unsigned {terminal.name} = {idx};\n")
        f.write(f"unsigned __IGNORE__ = {len(table.symbolList)};\n")
        f.write("} // end namespace Symbol\n\n")

        f.write("const std::vector<std::string> SYMBOL_LOOKUP = {\n")
        for symbol in table.symbolList:
            f.write(f'   "{symbol.name}",\n')
        f.write('    "__IGNORE__"\n')
        f.write("}; // End SYMBOL_LOOKUP\n\n")

        f.write("const std::vector<TerminalDef> TERMINALS = {\n")

        def escape_regex(r: str) -> str:
            regex = re.sub(r"\\", r"\\\\", r)
            regex = re.sub(r'"', r'\\"', regex)
            return regex

        for idx, terminal in enumerate(table.terminals):
            regex = escape_regex(terminal.regex)
            f.write(f'    {{Symbol::{terminal.name}, "{regex}"}}')
            if idx < len(table.terminals) - 1:
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

        preproc = CPPPreproc(grammar)

        for idx, rule in enumerate(grammar.rules):
            code = preproc.preproc(rule)
            f.write(
                f"{returnType} r{idx}(std::vector<StackItemPtr> {ARG_VECTOR})\n"
                "{\n"
                f'#line {rule.codeLine} "{rule.file}"\n'
                f"    {code}\n"
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
