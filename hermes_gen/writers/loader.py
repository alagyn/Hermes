from .hermesHeader import writeHermesHeader
from hermes_gen.grammar import Grammar
from hermes_gen.directives import Directive


def writeLoader(headerFilename: str, implFilename: str, parseTableFilename: str, name: str, grammar: Grammar):
    returnType = grammar.directives[Directive.return_][0]
    with open(headerFilename, mode='w') as f:
        writeHermesHeader(f)
        lines = [
            "#pragma once",
            "#include <memory>",
            "#include <iostream>",
            "namespace hermes {",
            f"{returnType} parse_{name}(std::shared_ptr<std::istream> input);",
            "} // end namespace hermes"
        ]
        f.write("\n".join(lines))

    with open(implFilename, mode='w') as f:
        writeHermesHeader(f)
        lines = [
            f"#include <hermes/{name}_parser.h>",
            f"#include <hermes/{name}_parseTable.h>",
            "#include <hermes/parser.h>",
            f"{returnType} hermes::parse_{name}(std::shared_ptr<std::istream> input)",
            "{",
            "    auto scanner = hermes::Scanner::New(",
            "       input,",
            "       TERMINALS.data(),",
            "       TERMINALS.size(),",
            "       Symbol::__EOF__, Symbol::__IGNORE__",
            "    );",
            f"    auto parseTable = hermes::ParseTable<{returnType}>::New(",
            "       &PARSE_TABLE[0][0],",
            "       TABLE_COLS, TABLE_ROWS,",
            "       REDUCTIONS.data(),",
            "       REDUCTION_FUNCS.data(),",
            "       SYMBOL_LOOKUP.data()",
            "     );",
            "     return hermes::parse(scanner, parseTable);",
            "}",
        ]
        f.write("\n".join(lines))
