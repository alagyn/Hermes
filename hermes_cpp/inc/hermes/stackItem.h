#pragma once

#include <string>

namespace hermes {

typedef unsigned HState;

template<typename HermesReturn>
class StackItem
{
public:
    HState state;

    StackItem(HState state)
        : state(state)
    {
    }

    virtual std::string t() = 0;
    virtual HermesReturn nt() = 0;
};

} //namespace hermes