#pragma once

#include <hermes/errors.h>

#include <list>

namespace hermes {

class Match
{
public:
    bool match;
    bool partial;

    std::list<int> pos;

    Match(int startPos = 0)
        : match(false)
        , partial(false)
        , pos()
    {
        pos.push_back(startPos);
    }
};

/*
    This exception allows a quick exit when we successfully match the full string
*/
class EndOfString : public HermesError
{
public:
    EndOfString()
        : HermesError("End of string")
    {
    }

    const char* what() const noexcept override
    {
        return msg.c_str();
    }
};

} //namespace hermes