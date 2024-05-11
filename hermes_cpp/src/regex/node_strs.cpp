#include <hermes/regex/node.h>

#include <sstream>

// toStr Methods, here for decluttering

namespace hermes {

std::string AlterationNode::toStr()
{
    std::stringstream ss;
    ss << p1->toStr();
    ss << "|";
    ss << p2->toStr();
    return ss.str();
}

std::string ConcatNode::toStr()
{
    std::stringstream ss;
    ss << p1->toStr();
    ss << p2->toStr();
    return ss.str();
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

std::string GroupNode::toStr()
{
    std::stringstream ss;
    ss << "(" << p->toStr() << ")";
    return ss.str();
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

std::string DotNode::toStr()
{
    return std::string(1, '.');
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

std::string EndOfStringNode::toStr()
{
    return "$";
}

} //namespace hermes