#include <hermes/internal/regex/node.h>

#include <sstream>
#include <stack>

using namespace hermes;

LiteralNode::LiteralNode(char sym)
    : sym(sym)
{
}

bool LiteralNode::match(const char* str, Match& m)
{
    if(str[m.pos.top()] == 0)
    {
        m.partial = true;
        return false;
    }

    bool out = str[m.pos.top()] == sym;
    if(out)
    {
        ++m.pos.top();
    }
    return out;
}

CharClassNode::CharClassNode()
    : syms()
    , invert(false)
{
}

bool CharClassNode::match(const char* str, Match& m)
{
    if(str[m.pos.top()] == 0)
    {
        m.partial = true;
        return false;
    }

    const char val = str[m.pos.top()];

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
        ++m.pos.top();
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

bool DotNode::match(const char* str, Match& m)
{
    if(str[m.pos.top()] == 0)
    {
        m.partial = true;
        return false;
    }

    ++m.pos.top();
    return true;
}

ConcatNode::ConcatNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

bool ConcatNode::match(const char* str, Match& m)
{
    /*
    repetition notes:
        a new repetition can only happen in p1.
        After we call p1->match(), if it was a repetition, it will
        have pushed every repetition it consumed onto the pos stack.
        Therefore, we only need to loop p2, popping one pos off the stack
        if it fails, until we get back to where we started
    */
    size_t startSize = m.pos.size();

    if(p1->match(str, m))
    {
        while(true)
        {
            // check if p2 matches
            bool out = p2->match(str, m);
            // exit if we matched
            if(out)
            {
                return true;
            }
            // else try to pop 1 repetition of p1 off
            else if(m.pos.size() > startSize)
            {
                m.pos.pop();
                // loop
            }
            // else we have no more repetitions, fail
            else
            {
                return false;
            }
        }
    }
    else
    {
        return false;
    }

    // should never get here...
    return false;
}

AlterationNode::AlterationNode(NodePtr p1, NodePtr p2)
    : p1(p1)
    , p2(p2)
{
}

bool AlterationNode::match(const char* str, Match& m)
{
    if(p1->match(str, m))
    {
        return true;
    }
    if(p2->match(str, m))
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

bool RepetitionNode::match(const char* str, Match& m)
{
    int matches = 0;

    size_t startSize = m.pos.size();

    // Loop until max matches, or maybe forever
    while(max == -1 || matches < max)
    {
        // only push once we get above the min
        // this prevents us backtracking below the min
        if(matches >= min)
        {
            m.pos.push(m.pos.top());
        }

        // Break when we don't get a match
        if(!p->match(str, m))
        {
            // if we pushed
            if(matches >= min)
            {
                // go back to the last good position
                m.pos.pop();
            }
            break;
        }

        ++matches;
    }

    // we just exited the loop, either we hit max matches
    // or we went as far as we could

    // we can't have gone over the max matches because of the loop limits
    // check if we were in the correct range
    if(min <= matches)
    {
        // we matched as much as we could, and were within the limits
        // if we failed before the max, we already reset the position back one step
        return true;
    }

    // If we are less than the minimum, take none of it
    // have to pop off the matches we made
    size_t numToPop = m.pos.size() - startSize;
    for(size_t i = 0; i < numToPop; ++i)
    {
        m.pos.pop();
    }
    return false;
}

GroupNode::GroupNode(NodePtr p)
    : p(p)
{
}

bool GroupNode::match(const char* str, Match& m)
{
    return p->match(str, m);
}

LookAheadNode::LookAheadNode(NodePtr p, bool negative)
    : p(p)
    , negative(negative)
{
}

bool LookAheadNode::match(const char* str, Match& m)
{
    // copy the current state
    Match start = m;
    // pass copy instead of m
    // this is so we don't accidentally set the partial flag
    // and that none of the str is consumed
    bool good = p->match(str, start);
    return good ^ negative;
}

bool EndOfStringNode::match(const char* str, Match& m)
{
    return str[m.pos.top()] == 0;
}
