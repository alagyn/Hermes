#include <hermes/regex/node.h>

#include <sstream>

using namespace hermes;

LiteralNode::LiteralNode(char sym)
    : sym(sym)
{
}

bool LiteralNode::match(const char* str, int& pos)
{
    if(str[pos] == 0)
    {
        return false;
    }

    bool out = str[pos] == sym;
    if(out)
    {
        ++pos;
    }
    return out;
}

std::string LiteralNode::toStr()
{
    std::stringstream ss;

    ss << (char)0x1B << "[4m";

    switch(sym)
    {
    case '\n':
        ss << "\\n";
        break;
    case '*':
    case '?':
    case '+':
    case '{':
    case '}':
    case '[':
    case '\\':
        ss
            //<< "\\"
            << sym;
        break;
    default:
        ss << sym;
        break;
    }

    ss << (char)0x1B << "[0m";
    //ss << sym;

    return ss.str();
}

CharClassNode::CharClassNode()
    : syms()
    , invert(false)
{
}

bool CharClassNode::match(const char* str, int& pos)
{
    if(str[pos] == 0)
    {
        return false;
    }

    const char val = str[pos];

    bool found = false;
    for(const char x : syms)
    {
        if(val == x)
        {
            found = true;
            break;
        }
    }

    bool out = found ^ invert;
    if(out)
    {
        ++pos;
    }
    return out;
}

void CharClassNode::pushRange(char s, char e)
{
    for(char x = s; x <= e; ++x)
    {
        syms.push_back(x);
    }
}

std::string CharClassNode::toStr()
{
    std::stringstream ss;
    ss << '[';
    if(invert)
    {
        ss << '^';
    }
    for(char x : syms)
    {
        if(x == '[' || x == ']' || x == '\\')
        {
            ss << '\\';
        }
        ss << x;
    }

    ss << ']';
    return ss.str();
}

DotNode::DotNode()
{
}

bool DotNode::match(const char* str, int& pos)
{
    if(str[pos] == 0)
    {
        return false;
    }

    ++pos;
    return true;
}

std::string DotNode::toStr()
{
    return std::string(1, '.');
}

ConcatNode::ConcatNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

bool ConcatNode::match(const char* str, int& pos)
{
    if(p1->match(str, pos))
    {
        return p2->match(str, pos);
    }

    return false;
}

std::string ConcatNode::toStr()
{
    std::stringstream ss;
    ss << p1->toStr();
    ss << p2->toStr();
    return ss.str();
}

AlterationNode::AlterationNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

bool AlterationNode::match(const char* str, int& pos)
{
    if(p1->match(str, pos))
    {
        return true;
    }
    if(p2->match(str, pos))
    {
        return true;
    }

    return false;
}

std::string AlterationNode::toStr()
{
    std::stringstream ss;
    ss << p1->toStr();
    ss << "|";
    ss << p2->toStr();
    return ss.str();
}

RepetitionNode::RepetitionNode(NodePtr p, int min, int max)
    : p(p)
    , min(min)
    , max(max)
{
}

bool RepetitionNode::match(const char* str, int& pos)
{
    int matches = 0;

    // Loop until max matches, or maybe forever
    while(max == -1 || matches < max)
    {
        int curPos = pos;
        // Break when we don't get a match
        if(!p->match(str, pos))
        {
            // reset back to the start of the current match
            pos = curPos;
            break;
        }

        ++matches;
    }

    // If we are less than the minimum, take none of it
    if(matches < min)
    {
        return false;
    }

    // Else, we can't have gone over the max, everything is fine
    return true;
}

std::string RepetitionNode::toStr()
{
    std::stringstream ss;
    ss << p->toStr();
    if(min == 0 && max == 1)
    {
        ss << "?";
    }
    else if(min == 0 && max == -1)
    {
        ss << "*";
    }
    else if(min == 1 && max == -1)
    {
        ss << "+";
    }
    else
    {
        ss << "{" << min;
        if(min != max)
        {
            ss << "," << max;
        }
        ss << "}";
    }

    return ss.str();
}

GroupNode::GroupNode(NodePtr p)
    : p(p)
{
}

bool GroupNode::match(const char* str, int& pos)
{
    return p->match(str, pos);
}

std::string GroupNode::toStr()
{
    std::stringstream ss;
    ss << "(" << p->toStr() << ")";
    return ss.str();
}

LookAheadNode::LookAheadNode(NodePtr p, bool negative)
    : p(p)
    , negative(negative)
{
}

bool LookAheadNode::match(const char* str, int& pos)
{
    int startPos = pos;
    bool good = p->match(str, pos);
    pos = startPos;
    return good ^ negative;
}

std::string LookAheadNode::toStr()
{
    std::stringstream ss;
    ss << "(?";
    if(negative)
    {
        ss << "!";
    }
    else
    {
        ss << "=";
    }

    ss << p->toStr() << ")";

    return ss.str();
}