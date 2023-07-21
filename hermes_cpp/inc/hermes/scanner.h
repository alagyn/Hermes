#pragma once

#include <fstream>
#include <string>

#include <hermes/_defaults.h>

namespace hermes {

enum class Symbol;

typedef struct
{
    Symbol symbol;
    std::string text;
    unsigned lineNum;
    unsigned charNum;
} ParseToken;

class Scanner

{
public:
    // TODO change this to istream
    Scanner(std::string filename);
    ~Scanner();

    ParseToken nextToken();

private:
    std::fstream handle;

    int curLineNum;
    int curCharNum;

    void consumeNewLine(char& nextChar);
};

} //namespace hermes