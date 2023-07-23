#include <hermes/errors.h>
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

    // Create input stream, pass our cmd line arg to it
    auto ssPtr = std::make_shared<stringstream>(argv[1]);
    // Create a scanner for the stream
    auto scanner = std::make_shared<hermes::Scanner>(ssPtr);
    // Create the parser
    hermes::Parser parser;
    // Parse the stream
    try
    {
        int out = parser.parse(scanner);
        // Print the result
        cout << "Result: " << out << "\n";
    }
    catch(const HermesError& err)
    {
        cout << "Error: " << err.what() << "\n";
    }
}