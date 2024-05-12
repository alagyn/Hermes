#include <hermes/internal/regex/node.h>

#include <sstream>
#include <stack>

using namespace hermes;

LiteralNode::LiteralNode(char sym)
    : sym(sym)
{
}

void LiteralNode::match(const char* str, Match& m)
{
    auto iter = m.pos.begin();
    auto end = m.pos.end();
    while(iter != end)
    {
        int pos = *iter;
        if(str[pos] == 0)
        {
            // mark partial if we hit end of string
            m.partial = true;
        }

        if(str[pos] != sym)
        {
            auto d = iter;
            ++iter;
            m.pos.erase(d);
        }
        else
        {
            // it was valid, inc the pos by 1
            *iter += 1;
            ++iter;
        }
    }
}

CharClassNode::CharClassNode()
    : syms()
    , invert(false)
{
}

void CharClassNode::match(const char* str, Match& m)
{
    auto iter = m.pos.begin();
    auto end = m.pos.end();
    while(iter != end)
    {
        const int pos = *iter;
        const char val = str[pos];
        if(val == 0)
        {
            m.partial = true;
        }

        bool found = false;
        for(const char x : syms)
        {
            if(val == x)
            {
                found = true;
                break;
            }
        }

        if((found && !invert) || (!found && invert))
        {
            *iter += 1;
            ++iter;
        }
        else
        {
            auto d = iter;
            ++iter;
            m.pos.erase(d);
        }
    }
}

void CharClassNode::pushRange(char s, char e)
{
    for(char x = s; x <= e; ++x)
    {
        syms.push_back(x);
    }
}

void DotNode::match(const char* str, Match& m)
{
    auto iter = m.pos.begin();
    auto end = m.pos.end();
    while(iter != end)
    {
        const char val = str[*iter];
        if(val == 0)
        {
            m.partial = true;
            auto d = iter;
            ++iter;
            m.pos.erase(d);
        }
        else
        {
            *iter += 1;
            ++iter;
        }
    }
}

ConcatNode::ConcatNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

void ConcatNode::match(const char* str, Match& m)
{
    p1->match(str, m);

    if(m.pos.empty())
    {
        return;
    }

    p2->match(str, m);
}

AlterationNode::AlterationNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

void AlterationNode::match(const char* str, Match& m)
{
    std::list<int> newPos;

    // Check the first alternation
    auto iter = m.pos.begin();
    auto end = m.pos.end();
    while(iter != end)
    {
        int pos = *iter;
        Match x(pos);
        p1->match(str, x);

        for(int p : x.pos)
        {
            newPos.push_back(p);
        }

        m.partial = m.partial || x.partial;
        ++iter;
    }

    // Check the second alternation
    iter = m.pos.begin();
    end = m.pos.end();
    while(iter != end)
    {
        int pos = *iter;
        Match x(pos);
        p2->match(str, x);

        for(int p : x.pos)
        {
            newPos.push_back(p);
        }

        m.partial = m.partial || x.partial;
        ++iter;
    }

    // newPos becomes the new list of pos
    m.pos.swap(newPos);
}

RepetitionNode::RepetitionNode(NodePtr p, int min, int max)
    : p(p)
    , min(min)
    , max(max)
{
}

void RepetitionNode::match(const char* str, Match& m)
{
    std::list<int> newPos;

    auto iter = m.pos.begin();
    auto end = m.pos.end();
    while(iter != end)
    {
        recurse(str, newPos, *iter, 0, m.partial);
        ++iter;
    }

    m.pos.swap(newPos);
}

void RepetitionNode::recurse(
    const char* str,
    std::list<int>& out,
    int curPos,
    int curMatch,
    bool& partial
)
{
    if(curMatch >= min)
    {
        out.push_back(curPos);
    }

    if(str[curPos] == 0)
    {
        partial = true;
        return;
    }

    if(curMatch == max)
    {
        return;
    }

    Match m(curPos);
    // Do a SINGLE match of the sub-pattern
    p->match(str, m);
    partial |= m.partial;

    auto iter = m.pos.begin();
    auto end = m.pos.end();
    // Recurse and check every new possible pos for another match
    while(iter != end)
    {
        int nextPos = *iter;
        // prevent infinite loops
        if(nextPos != curPos)
        {
            recurse(str, out, *iter, curMatch + 1, partial);
        }
        ++iter;
    }
}

GroupNode::GroupNode(NodePtr p)
    : p(p)
{
}

void GroupNode::match(const char* str, Match& m)
{
    p->match(str, m);
}

LookAheadNode::LookAheadNode(NodePtr p, bool negative)
    : p(p)
    , negative(negative)
{
}

void LookAheadNode::match(const char* str, Match& m)
{
    auto iter = m.pos.begin();
    auto end = m.pos.end();
    while(iter != end)
    {
        Match x(*iter);
        p->match(str, x);

        if((x.pos.empty() && !negative) || (!x.pos.empty() && negative))
        {
            auto d = iter;
            ++iter;
            m.pos.erase(d);
        }
        else
        {
            ++iter;
        }
    }
}

void EndOfStringNode::match(const char* str, Match& m)
{
    auto iter = m.pos.begin();
    auto end = m.pos.end();
    while(iter != end)
    {
        int pos = *iter;
        if(str[pos] == 0)
        {
            throw EndOfString();
        }
        else
        {
            auto d = iter;
            ++iter;
            m.pos.erase(d);
        }
    }
}
