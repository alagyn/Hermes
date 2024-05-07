#include <hermes/regex/regex.h>

#include <hermes/errors.h>
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

Match Regex::match(const std::string& str) const
{
    return match(str.c_str());
}

Match Regex::match(const char* str) const
{
    int pos = 0;
    if(str[pos] == 0)
    {
        throw HermesError("Regex::match() Cannot match empty string");
    }
    Match out;
    bool fullmatch = root->match(str, out);

    out.match = fullmatch;
    // unset partial if we matched the whole thing
    out.partial = !fullmatch && out.partial;

    return out;
}

std::string Regex::toStr() const
{
    return root->toStr();
}