# Hermes

<img src="docs/images/hermes-logo-256.png" align="right">

A Context-Free-Grammar parser generator for C++ written in Python.
It's like Bison's estranged younger brother.

## More docs coming soon

### Compiling and linking to your app

```cmake

set(GRAMMAR "yourGrammerFile.hm")
add_subdirectory(hermes)

target_link_libraries(yourTarget hermes)

```

### A minimal example: The amazing calculator

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
#include <hermes/parser.h>
#include <hermes/scanner.h>

#include <iostream>
#include <sstream>

using namespace std;

int main(int argc, char** argv)
{
    if(argc != 2)
    {
        cout << "Usage: calculator 'expr'\n";
        return 1;
    }

    auto ssPtr = std::make_shared<stringstream>();
    stringstream& ss = *ssPtr;

    ss << argv[1];

    auto scanner = std::make_shared<hermes::Scanner>(ssPtr);
    hermes::Parser parser;

    int out = parser.parse(scanner);

    cout << "Result: " << out << "\n";
}
```