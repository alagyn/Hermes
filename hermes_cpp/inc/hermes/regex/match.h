#pragma once

namespace hermes {

class Match
{
public:
    bool match;
    bool partial;
    int pos;

    Match()
        : match(false)
        , partial(false)
        , pos(0)
    {
    }
};

} //namespace hermes