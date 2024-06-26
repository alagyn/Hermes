#include <hermes/internal/regex/rparser.h>

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
NodePtr parseBracketRepetition(const char* str, int& pos, NodePtr inner);
NodePtr parseGroup(const char* str, int& pos);
NodePtr parseCharClass(const char* std, int& pos);

#define THROW(loc, msg) \
    { \
        std::stringstream ss; \
        ss << (loc) << ": REGEX \"" << str << "\" char " << pos << ": " << msg; \
        throw HermesError(ss.str()); \
    }

bool isOrdinary(char c)
{
    return !strchr(".^$*?+|()[{", c);
}

// top level parse function
NodePtr hermes::parseRegexPattern(const char* str)
{
    int pos = 0;
    if(str[pos] == 0)
    {
        THROW("rparser::parseRegexPattern", "Empty string is not valid regex");
    }
    NodePtr regex = parseAlternation(str, pos);

    if(!regex)
    {
        THROW("rparser::parserRegexPattern()", "Failed to parse regex");
    }
    else if(pos != -1)
    {
        THROW(
            "rparser::parserRegexPattern()",
            "Failed to parse regex, did not parse the entire string: "
                << regex->toStr()
        );
    }

    if(!regex || pos != -1)
    {
        THROW(
            "rparser::parseRegexPattern()",
            "uhoh, something returned null or we didn't parse the entire regex "
            "str"
        );
    }

    // concat a EOS to the pattern
    auto eos = std::make_shared<EndOfStringNode>();
    regex = std::make_shared<ConcatNode>(regex, eos);

    return regex;
}

NodePtr parseAlternation(const char* str, int& pos)
{
    NodePtr p1 = parseConcat(str, pos);

    // Check for additional alternations
    while(p1 && pos >= 0 && str[pos] == '|')
    {
        // inc past the bar
        ++pos;
        // check for EOS
        if(str[pos] == 0)
        {
            THROW(
                "rparser::parseAlternation()",
                " expected pattern after |, but found end of string"
            );
        }

        NodePtr p2 = parseConcat(str, pos);

        if(!p2)
        {
            THROW(
                "rparser::parseAlternation()",
                " failed to parse alternate pattern"
            );
        }

        p1 = std::make_shared<AlterationNode>(p1, p2);
    }

    return p1;
}

NodePtr parseConcat(const char* str, int& pos)
{
    NodePtr p1 = parseRepetition(str, pos);

    /*
        Recursively call parseConcat so we always
        have concats on the right. This makes repetition
        easier to backtrack with the stack
     */
    if(p1 && pos >= 0 && str[pos] != '|' && str[pos] != ')')
    {
        NodePtr p2 = parseConcat(str, pos);
        if(p2)
        {
            return std::make_shared<ConcatNode>(p1, p2);
        }
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
        ++pos;
        out = std::make_shared<RepetitionNode>(inner, 0, -1);
        break;
    case '+':
        ++pos;
        out = std::make_shared<RepetitionNode>(inner, 1, -1);
        break;
    case '?':
        ++pos;
        out = std::make_shared<RepetitionNode>(inner, 0, 1);
        break;
    case '{':
        ++pos;
        out = parseBracketRepetition(str, pos, inner);
        break;
    default:
        // default nothing
        break;
    }

    if(out)
    {
        return recurseRepetition(str, pos, out);
    }

    // No repetition
    return inner;
}

NodePtr parseRepetition(const char* str, int& pos)
{
    NodePtr p = parseAtomicNode(str, pos);

    if(p && pos >= 0)
    {
        // attempt to parse repetition marks
        p = recurseRepetition(str, pos, p);
    }

    return p;
}

NodePtr parseAtomicNode(const char* str, int& pos)
{
    char c = str[pos++];

    if(c == 0)
    {
        pos = -1;
        // return null
        return std::shared_ptr<Node>();
    }

    if(c == '\\')
    {
        return parseEscapeSequence(str, pos);
    }

    if(isOrdinary(c))
    {
        return std::make_shared<LiteralNode>(c);
    }

    if(c == '(')
    {
        return parseGroup(str, pos);
    }

    if(c == '[')
    {
        NodePtr out = parseCharClass(str, pos);
        ++pos;
        return out;
    }

    if(c == '.')
    {
        return std::make_shared<DotNode>();
    }

    THROW(
        "rparser::parseAtomicNode()",
        "Invalid pattern, expected atomic, got unknown '"
            << c << "' (" << static_cast<int>(c) << ")"
    );
    ;
}

NodePtr parseEscapeSequence(const char* str, int& pos)
{
    char c = str[pos++];

    if(c == 'n')
    {
        return std::make_shared<LiteralNode>('\n');
    }
    else if(c == 't')
    {
        return std::make_shared<LiteralNode>('\t');
    }

    auto out = std::make_shared<CharClassNode>();
    // class ranges
    if(c == 'd')
    {
        out->pushRange('0', '9');
    }
    else if(c == 'l')
    {
        out->pushRange('a', 'z');
    }
    else if(c == 'u')
    {
        out->pushRange('A', 'Z');
    }
    else if(c == 's')
    {
        out->syms.push_back(' ');
        out->syms.push_back('\t');
        out->syms.push_back('\n');
    }
    else
    {
        // Return a literal if not a known class
        return std::make_shared<LiteralNode>(c);
    }

    return out;
}

NodePtr parseGroup(const char* str, int& pos)
{
    bool isLA = false;
    bool negative = false;
    if(str[pos] == '?')
    {
        char c = str[++pos];
        isLA = true;
        if(c == '!')
        {
            negative = true;
        }
        else if(c != '=')
        {
            THROW(
                "rparser::parseGroup()",
                "Invalid look-ahead specifier, expected '=' or '!', found '"
                    << c << "' (" << static_cast<int>(c) << ")"
            );
        }

        // inc past specifier
        ++pos;
    }
    NodePtr internal = parseAlternation(str, pos);
    if(!internal || pos == -1)
    {
        THROW("rparser::parseGroup()", "Empty parenthesis is not allowed");
    }

    NodePtr out;
    if(isLA)
    {
        out = std::make_shared<LookAheadNode>(internal, negative);
    }
    else
    {
        out = std::make_shared<GroupNode>(internal);
    }

    // inc past closing parenthesis
    ++pos;

    return out;
}

NodePtr parseCharClass(const char* str, int& pos)
{
    auto out = std::make_shared<CharClassNode>();
    char c = str[pos];

    // invert if first char is ^
    if(c == '^')
    {
        out->invert = true;
        c = str[++pos];
    }

    while(c != ']')
    {
        if(c == 0)
        {
            THROW(
                "rparser::parseCharClass()",
                " Expected closing bracket ']' but found end of string"
            )
        }

        if(c == '\\')
        {
            ++pos;
            auto escapedNode = parseEscapeSequence(str, pos);

            // check if it was a literal
            {
                auto node = std::dynamic_pointer_cast<LiteralNode>(escapedNode);
                if(node)
                {
                    out->syms.push_back(node->sym);
                    c = str[pos];
                    continue;
                }
            }
            // else it was a new char class
            {
                auto node =
                    std::dynamic_pointer_cast<CharClassNode>(escapedNode);
                if(!node)
                {
                    throw HermesError("rparser::parseCharClass() Bad pointer "
                                      "cast from parseEscapeSequence()");
                }

                std::copy(
                    node->syms.begin(),
                    node->syms.end(),
                    std::back_inserter(out->syms)
                );
            }
            c = str[pos];
            continue;
        }
        else if(c == '-' && !out->syms.empty())
        {
            // Handle char ranges
            // get next char
            c = str[pos + 1];
            char prev = out->syms.back();
            bool good = false;
            if('a' <= prev && prev <= 'z' && 'a' <= c && c <= 'z')
            {
                good = true;
            }

            if('A' <= prev && prev <= 'Z' && 'A' <= c && c <= 'Z')
            {
                good = true;
            }

            if('0' <= prev && prev <= '9' && '0' <= c && c <= '9')
            {
                good = true;
            }

            if(good)
            {
                // prev + 1 since it was already added
                ++pos;
                out->pushRange(prev + 1, c);
            }
            else
            {
                // Not a valid range, just use the dash as a literal
                out->syms.push_back('-');
            }
        }
        else
        {
            out->syms.push_back(c);
        }

        c = str[++pos];
    }

    if(out->syms.empty())
    {
        THROW("rparser::parseCharClass()", "Empty character class is invalid");
    }

    return out;
}

int readNum(const char* str, int& pos)
{
    std::vector<char> vals;
    while('0' <= str[pos] && str[pos] <= '9')
    {
        vals.push_back(str[pos++]);
    }

    if(vals.empty())
    {
        THROW(
            "rparser::readNum()",
            "Expected number, got '" << str[pos] << "' ("
                                     << static_cast<int>(str[pos]) << ")"
        );
    }

    int out = 0;

    for(int i = 0; i < vals.size(); ++i)
    {
        int digit = static_cast<int>(vals[i] - '0');
        for(int exp = 1; exp < vals.size() - i; ++exp)
        {
            digit *= 10;
        }

        out += digit;
    }

    return out;
}

NodePtr parseBracketRepetition(const char* str, int& pos, NodePtr inner)
{
    int min = 0, max = -1;

    // skip initial whitespace
    char c = str[pos];
    while(c == ' ')
    {
        c = str[++pos];
    }

    if(c == 0)
    {
        THROW(
            "rparser::parseBracketRepetition()",
            " Invalid bracket repetition, expected number, but found "
            "end of string"
        );
    }
    else if(c < '0' || c > '9')
    {
        THROW(
            "rparser::parseBracketRepetition()",
            " Invalid bracket repetition, expected comma or number, but found '"
                << c << "' (" << static_cast<int>(c) << ")"
        );
    }

    min = readNum(str, pos);
    c = str[pos];
    while(c == ' ')
    {
        c = str[++pos];
    }

    if(c == '}')
    {
        max = min;
    }
    else if(c == ',')
    {
        c = str[++pos];
        while(c == ' ')
        {
            c = str[++pos];
        }

        // if {3,}, min = 3, max = -1
        if(c != '}')
        {
            if(c < '0' || c > '9')
            {
                THROW(
                    "rparser::parseBracketRepetition()",
                    " Invalid bracket repetition, expected number, but "
                    "found '"
                        << c << "' (" << static_cast<int>(c) << ")"
                );
            }

            max = readNum(str, pos);
            c = str[pos];
            while(c == ' ')
            {
                c = str[++pos];
            }

            if(c != '}')
            {
                THROW(
                    "rparser::parseBracketRepetition()",
                    " Invalid bracket repetition, expected closing bracket "
                    "'}', "
                    "but "
                    "found '"
                        << c << "' (" << static_cast<int>(c) << ")"
                );
            }
        }
    }
    else
    {
        THROW(
            "rparser::parseBracketRepetition()",
            " Invalid bracket repetition, expected comma or closing bracket "
            "'}', but found '"
                << c << "' (" << static_cast<int>(c) << ")"
        );
    }

    // skip closing bracket
    ++pos;

    return std::make_shared<RepetitionNode>(inner, min, max);
}
