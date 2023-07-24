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
    ParseToken _nextToken();

    char get();
    void unget();

    std::shared_ptr<std::istream> handle;
    unsigned lineNum;
    unsigned charNum;
    unsigned lastLineLength;
};

} //namespace hermes