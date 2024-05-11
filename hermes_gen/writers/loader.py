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
            "#include <hermes/parser.h>",
            "namespace hermes {",
            ""
            f"std::shared_ptr<Parser<{returnType}>> load_{name}();",
            "} // end namespace hermes"
        ]
        f.write("\n".join(lines))

    with open(implFilename, mode='w') as f:
        writeHermesHeader(f)
        lines = [
            f"#include <hermes/{name}_loader.h>",
            f"#include <hermes/{name}_grammar.h>",
            f"#include <hermes/internal/grammar.h>",
            "namespace hermes {",
            # force template to instantiate
            f"template class Parser<{returnType}>;"
            f"std::shared_ptr<Parser<{returnType}>> load_{name}()",
            "{",
            f"    auto grammar =  Grammar<{returnType}>::New(",
            "       &PARSE_TABLE[0][0],",
            "       TABLE_COLS, TABLE_ROWS,",
            "       REDUCTIONS.data(),",
            "       REDUCTION_FUNCS.data(),",
            "       SYMBOL_LOOKUP.data(),",
            "       TERMINALS.data(),",
            "       TERMINALS.size(),",
            "       Symbol::__EOF__, Symbol::__IGNORE__",
            "    );",
            f"    return std::make_shared<Parser<{returnType}>>(grammar);"
            "}",
            "}"
        ]
        f.write("\n".join(lines))
