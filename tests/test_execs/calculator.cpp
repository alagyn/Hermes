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