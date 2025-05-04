from hermes_gen.writers.hermesHeader import writeHermesHeader
from hermes_gen.grammar import Grammar
from hermes_gen.directives import Directive

# TODO how to handle more than one grammar?


def writePybindModule(filename: str, grammar: Grammar, name: str):
    with open(filename, mode='w') as f:
        writeHermesHeader(f)

        f.write(
            "#include <hermes/internal/bind-hermes-py.h>\n"
            f"#include <hermes/{name}_loader.h>\n"
            "\n"
            "using namespace hermes;\n\n"
        )

        returnType = grammar.directives[Directive.return_][0]

        f.write(
            f"PyParser<{returnType}>* py_load_{name}()\n"
            "{\n"
            f"     return new PyParser<{returnType}>(hermes::load_{name}());\n"
            "}\n\n"
        )

        f.write(
            f"PYBIND11_MODULE(hermes_{name}, m)\n"
            "{\n"
            f"    init_hermes<{returnType}>(m);\n"
            f'    m.def("load_{name}", py_load_{name});\n'
            "}\n"
        )
