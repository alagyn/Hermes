#pragma once

#include <istream>
#include <memory>
#include <string>

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
    std::shared_ptr<Scanner> New(std::shared_ptr<std::istream> handle);

    Scanner(std::shared_ptr<std::istream> handle);

    ParseToken nextToken();

private:
    std::shared_ptr<std::istream> handle;

    int curLineNum;
    int curCharNum;

    void consumeNewLine(char& nextChar);
};

} //namespace hermes