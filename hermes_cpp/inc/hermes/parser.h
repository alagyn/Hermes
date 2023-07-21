#pragma once

#include <deque>
#include <memory>

#include <hermes/_defaults.h>
#include <hermes/scanner.h>

namespace hermes {

typedef unsigned HState;

class StackItem;
using StackItemPtr = std::shared_ptr<StackItem>;

class Parser
{
public:
    HERMES_RETURN parse(std::shared_ptr<Scanner> scanner);

private:
    std::deque<StackItemPtr> stack;
};

} //namespace hermes