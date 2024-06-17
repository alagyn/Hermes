#pragma once

#include <hermes/internal/regex/regex.h>

#include <istream>
#include <memory>
#include <string>

namespace hermes {

struct Location
{
    unsigned lineStart;
    unsigned charStart;
    unsigned lineEnd;
    unsigned charEnd;
};

struct ParseToken
{
    unsigned symbol;
    std::string text;
    Location loc;
};

struct Terminal
{
    // Symbol ID
    unsigned id;
    Regex re;
};

class Scanner
{
public:
    static std::shared_ptr<Scanner>
    New(std::shared_ptr<std::istream> handle,
        const Terminal* terminals,
        size_t numTerminals,
        unsigned symbolEOF,
        unsigned symbolIGNORE);

    Scanner(
        std::shared_ptr<std::istream> handle,
        const Terminal* terminals,
        size_t numTerminals,
        unsigned symbolEOF,
        unsigned symbolIGNORE
    );

    ParseToken nextToken();

private:
    ParseToken _nextToken();

    char get();
    void unget();

    std::shared_ptr<std::istream> handle;
    unsigned lineNum;
    unsigned charNum;
    unsigned lastLineLength;

    const unsigned symbolEOF;
    const unsigned symbolIGNORE;

    const Terminal* terminals;
    size_t numTerminals;
};

} //namespace hermes