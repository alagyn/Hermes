#pragma once

#include <stack>

namespace hermes {

class Match
{
public:
    bool match;
    bool partial;
    std::stack<int> pos;

    Match()
        : match(false)
        , partial(false)
        , pos()
    {
        pos.push(0);
    }
};

} //namespace hermes