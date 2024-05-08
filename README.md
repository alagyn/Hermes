# Hermes

<img src="docs/images/hermes-logo-256.png" align="right">

A Context-Free-Grammar parser generator for C++ written in Python.
It's like Bison's estranged younger brother.

### [Read the docs](docs)

## Compiling and linking to your app

```cmake

set(GRAMMAR "yourGrammerFile.hm")
add_subdirectory(hermes)

target_link_libraries(yourTarget hermes)

```

## A minimal example: The amazing calculator

Grammer:
```
%return int
%include <iostream>

INT = "[0-9]+";
PLUS = "\+";
MINUS = "-";
STAR = "\*";
SLASH = "/";
OPEN_PAREN = "\(";
CLOSE_PAREN = "\)";

output = expr { return $0; };

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
    | term { return $0; }
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
    | factor { return $0; }
    ;

factor
    = INT { return std::stoi($0); }
    | OPEN_PAREN expr CLOSE_PAREN { return $1; }
    ;
```

App:
```c++
#include <hermes/calc_parser.h>
#include <hermes/errors.h>

#include <iostream>
#include <sstream>

using namespace std;

void parse(const std::string& str)
{
    // Create a scanner for the stream
    auto input = std::make_shared<stringstream>(str);
    // Parse the stream
    try
    {
        int out = hermes::parse_calc(input);
        // Print the result
        cout << "Result: " << out << "\n";
    }
    catch(const HermesError& err)
    {
        cout << "Error: " << err.what() << "\n";
    }
}

int main(int argc, char** argv)
{
    while(true)
    {
        char str[256];
        std::cout << "> ";
        cin.getline(str, 256);
        parse(std::string(str));
    }

    return 0;
}#include <hermes/calc_parser.h>
#include <hermes/errors.h>

#include <iostream>
#include <sstream>

using namespace std;

void parse(const std::string& str)
{
    // Create a scanner for the stream
    auto input = std::make_shared<stringstream>(str);
    // Parse the stream
    try
    {
        int out = hermes::parse_calc(input);
        // Print the result
        cout << "Result: " << out << "\n";
    }
    catch(const HermesError& err)
    {
        cout << "Error: " << err.what() << "\n";
    }
}

int main(int argc, char** argv)
{
    // REPL
    while(true)
    {
        char str[256];
        std::cout << "> ";
        cin.getline(str, 256);
        parse(std::string(str));
    }

    return 0;
}
```