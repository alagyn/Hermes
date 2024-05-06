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

bool Regex::match(const std::string& str) const
{
    return match(str.c_str());
}

bool Regex::match(const char* str) const
{
    int pos = 0;
    bool good = root->match(str, pos);
    // make sure we matched the full string
    return good && str[pos] == 0;
}

bool Regex::match(const std::string& str, bool& partial) const
{
    return match(str.c_str(), partial);
}

bool Regex::match(const char* str, bool& partial) const
{
    int pos = 0;
    bool good = root->match(str, pos);
    partial = str[pos] == 0;
    return good;
}

std::string Regex::toStr() const
{
    return root->toStr();
}