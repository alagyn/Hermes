#include <hermes/errors.h>
#include <hermes/parser.h>
#include <hermes/scanner.h>

#include <fstream>
#include <iostream>
#include <sstream>

using namespace std;

void parse(const std::string& str)
{
    // Create a scanner for the stream
    auto input = std::make_shared<stringstream>(str);
    auto scanner = hermes::Scanner::New(input);
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
}