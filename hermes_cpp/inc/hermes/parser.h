#pragma once

#include <deque>
#include <memory>

#include <hermes/scanner.h>
#include <hermes/symbol.h>

namespace hermes {

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