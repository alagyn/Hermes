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
    while(true)
    {
        char str[256];
        std::cout << "> ";
        cin.getline(str, 256);
        // Create a stream for the input
        auto input = std::make_shared<stringstream>(str);

        try
        {
            // parse the input
            int out = parser->parse(input);
            // print the result
            cout << "Result: " << out << "\n";
        }
        catch(const HermesError& err)
        {
            cout << "Error: " << err.what() << "\n";
        }
    }

    return 0;
}