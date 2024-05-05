#include <rparser.h>

#include <hermes/errors.h>

#include <cstring>
#include <sstream>

using namespace hermes;

// In order of precendence
NodePtr parseAlternation(const char* str, int& pos);
NodePtr parseConcat(const char* str, int& pos);
NodePtr parseRepetition(const char* str, int& pos);
NodePtr parseAtomicNode(const char* str, int& pos);
NodePtr parseEscapeSequence(const char* str, int& pos);
NodePtr parseBracketRepetition(const char* str, int& pos);
NodePtr parseCharClass(const char* std, int& pos);

bool isOrdinary(char c)
{
    return !strchr(".^$*?+|()[{", c);
}

// top level parse function
NodePtr parseRegexPattern(const char* str)
{
    int pos = 0;
    NodePtr regex = parseAlternation(str, pos);

    if(!regex || str[pos] != 0)
    {
        // TODO error if we failed or didn't consume the whole string
    }

    return regex;
}

NodePtr parseAlternation(const char* str, int& pos)
{
    NodePtr p1 = parseConcat(str, pos);

    // Check for additional alternations
    while(p1 && str[pos] == '|')
    {
        // inc past the bar
        ++pos;
        // check for EOS
        if(str[pos] == 0)
        {
            throw HermesError("rparser::parseAlternation() expected pattern "
                              "after |, but found end of string");
        }

        NodePtr p2 = parseConcat(str, pos);

        if(!p2)
        {
            throw HermesError(
                "rparser::parseAlternation() failed to parse alternate pattern"
            );
        }

        p1 = std::make_shared<AlterationNode>(p1, p2);
    }

    return p1;
}

NodePtr parseConcat(const char* str, int& pos)
{
    NodePtr p1 = parseRepetition(str, pos);

    while(str[pos] != 0 && str[pos] != '|' && str[pos] != ')')
    {
        NodePtr p2 = parseRepetition(str, pos);
        p1 = std::make_shared<ConcatNode>(p1, p2);
    }

    return p1;
}

// We can have 0 or more repetition marks after a pattern
NodePtr recurseRepetition(const char* str, int& pos, NodePtr inner)
{
    NodePtr out;

    char next = str[pos];

    switch(next)
    {
    case '*':
        out = std::make_shared<RepetitionNode>(inner, 0, -1);
        break;
    case '+':
        out = std::make_shared<RepetitionNode>(inner, 1, -1);
        break;
    case '?':
        out = std::make_shared<RepetitionNode>(inner, 0, 1);
        break;
    case '{':
        ++pos;
        out = parseBracketRepetition(str, pos);
        break;
    default:
        // default nothing
        break;
    }

    if(out)
    {
        ++pos;
        return recurseRepetition(str, pos, out);
    }

    // No repetition
    return inner;
}

NodePtr parseRepetition(const char* str, int& pos)
{
    NodePtr p = parseAtomicNode(str, pos);

    if(p && str[pos] != 0)
    {
        // attempt to parse repetition marks
        p = recurseRepetition(str, pos, p);
    }

    return p;
}

NodePtr parseAtomicNode(const char* str, int& pos)
{
    char c = str[pos];

    if(c == '\\')
    {
        ++pos;
        return parseEscapeSequence(str, pos);
    }

    if(isOrdinary(c))
    {
        return std::make_shared<LiteralNode>(c);
    }

    if(c == '(')
    {
        ++pos;
        NodePtr internal = parseAlternation(str, pos);
        NodePtr out = std::make_shared<GroupNode>(internal);
        // inc past closing parenthesis
        ++pos;
        return out;
    }

    if(c == '[')
    {
        ++pos;
        NodePtr out = parseCharClass(str, pos);
        ++pos;
        return out;
    }

    if(c == '.')
    {
        ++pos;
        return std::make_shared<DotNode>();
    }

    // TODO start/end line?
}

NodePtr parseEscapeSequence(const char* str, int& pos)
{
}