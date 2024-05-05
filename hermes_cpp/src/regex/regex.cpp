#include <hermes/regex/regex.h>

#include <hermes/regex/rparser.h>

using namespace hermes;

Regex::Regex(const std::string& pattern)
    : Regex(pattern.c_str())
{
}

Regex::Regex(const char* pattern)
    : root(parseRegexPattern(pattern))
{
}
