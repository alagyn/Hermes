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