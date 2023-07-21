#pragma once

#include <string>

#include <hermes/symbol.h>

namespace hermes {

typedef unsigned HState;

class StackItem
{
public:
    HState state;

    StackItem(HState state)
        : state(state)
    {
    }

    virtual std::string t() = 0;
    virtual HERMES_RETURN nt() = 0;
};

} //namespace hermes