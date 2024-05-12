#include <hermes/internal/regex/regex.h>

#include <iostream>

using namespace std;

int main(int argc, char** argv)
{
    if(argc < 2 || argc > 3)
    {
        cout << "Usage:\n";
        cout << "regex-debug [regex] <test-string>\n";
        return 1;
    }

    try
    {
        hermes::Regex r(argv[1]);
        cout << r.toStr() << endl;
        cout << r.annotate() << endl;

        if(argc == 3)
        {
            auto m = r.match(argv[2]);
            cout << "Fullmatch: " << m.match << " Partial:" << m.partial << endl;
        }
    }
    catch(const std::exception& err)
    {
        cout << "Error:" << err.what() << endl;
        return 1;
    }

    return 0;
}