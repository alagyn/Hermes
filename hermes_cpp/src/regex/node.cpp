#include <hermes/regex/node.h>

using namespace hermes;

LiteralNode::LiteralNode(char sym)
    : sym(sym)
{
}

bool LiteralNode::match(StrType str, int& pos)
{
    if(pos >= str.size())
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

CharClassNode::CharClassNode(const std::vector<char>& syms, bool invert)
    : syms(syms)
    , invert(invert)
{
}

bool CharClassNode::match(StrType str, int& pos)
{
    if(pos >= str.size())
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

DotNode::DotNode()
{
}

bool DotNode::match(StrType str, int& pos)
{
    if(pos >= str.size())
    {
        return false;
    }

    ++pos;
    return true;
}

ConcatNode::ConcatNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

bool ConcatNode::match(StrType str, int& pos)
{
    if(p1->match(str, pos))
    {
        return p2->match(str, pos);
    }

    return false;
}

AlterationNode::AlterationNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

bool AlterationNode::match(StrType str, int& pos)
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

RepetitionNode::RepetitionNode(NodePtr p, int min, int max)
    : p(p)
    , min(min)
    , max(max)
{
}

bool RepetitionNode::match(StrType str, int& pos)
{
    int startPos = pos;
    int matches = 0;

    // Loop until max matches, or maybe forever
    while(max == -1 || matches < max)
    {
        // Break when we don't get a match
        if(!p->match(str, pos))
        {
            break;
        }

        ++matches;
    }

    // If we are less than the minimum, take none of it
    if(matches < min)
    {
        pos = startPos;
        return false;
    }

    // Else, we can't have gone over the max, everything is fine
    return true;
}
