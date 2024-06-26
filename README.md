<table>
<tr>
<td>
<img src="docs/images/hermes-logo-256.png">
</td>
<td>

# Hermes

A Context-Free-Grammar parser generator for C++ written in Python.
It's like Bison's estranged younger brother.
</td>
</table>

### [Read the docs](docs)

## Compiling and linking to your app

```cmake

add_subdirectory(Hermes)

add_hermes_grammar(
    TARGET myParser
    GRAMMAR myGrammar.hm
)

target_link_libraries(yourTarget myParser)

```

See [the cmake docs](docs/cmake.md) for more info as well as build instructions

## A minimal example: The amazing calculator

Grammar:
```
%return int

%header %%
#include <iostream>

%%

INT = "[0-9]+";
PLUS = "\+";
MINUS = "-";
STAR = "\*";
SLASH = "/";
OPEN_PAREN = "\(";
CLOSE_PAREN = "\)";

output = expr;

expr
    = expr PLUS term
    {
        std::cout << $0 << " + " << $2 << "\n";
        return $0 + $2;
    }
    | expr MINUS term
    {
        std::cout << $0 << " - " << $2 << "\n";
        return $0 - $2;
    }
    | term
    ;

term
    = term STAR factor
    {
        std::cout << $0 << " * " << $2 << "\n";
        return $0 * $2;
    }
    | term SLASH factor
    {
        std::cout << $0 << " / " << $2 << "\n";
        return $0 / $2;
    }
    | factor
    ;

factor
    = INT { return std::stoi($0); }
    | OPEN_PAREN expr CLOSE_PAREN { return $1; }
    ;
```

App:
```c++
#include <hermes/calc_loader.h>
#include <hermes/errors.h>

#include <iostream>
#include <sstream>

using namespace std;

int main(int argc, char** argv)
{
    // Load grammar
    std::shared_ptr<hermes::Parser<int>> parser;
    try
    {
        parser = hermes::load_calc();
    }
    catch(const HermesError& err)
    {
        cout << "Error loading grammar: " << err.what();
        return 1;
    }

    // REPL
    while(cin.good())
    {
        char str[256];
        std::cout << "> ";
        cin.getline(str, 256);
        // Create a stream for the input
        auto input = std::make_shared<stringstream>(str);

        try
        {
            bool error = false;
            // parse the input
            int out = parser->parse(input, error);
            if(!error)
            {
                // print the result
                cout << "Result: " << out << "\n";
            }
            else
            {
                cout << "Error\n";
            }
        }
        catch(const std::exception& err)
        {
            cout << err.what() << "\n";
        }
    }

    return 0;
}
```