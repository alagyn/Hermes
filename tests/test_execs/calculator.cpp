#include <hermes/errors.h>
#include <hermes/parser.h>
#include <hermes/scanner.h>

#include <fstream>
#include <iostream>
#include <sstream>

using namespace std;

void usage()
{
    cout << "Usage: \n";
    cout << "    calculator -e \"expr\"\n";
    cout << "    calculator -f [filename]\n";
}

int main(int argc, char** argv)
{
    if(argc != 3)
    {
        usage();
        return 1;
    }

    string type(argv[1]);

    std::shared_ptr<istream> input;

    // Create input stream, pass our cmd line arg to it
    if(type == "-e")
    {
        input = std::make_shared<stringstream>(argv[2]);
    }
    else if(type == "-f")
    {
        input = std::make_shared<ifstream>(argv[2]);
        if(!input->good())
        {
            cout << "Cannot open file\n";
            usage();
            return 2;
        }
    }
    else
    {
        usage();
    }

    // Create a scanner for the stream
    auto scanner = std::make_shared<hermes::Scanner>(input);
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