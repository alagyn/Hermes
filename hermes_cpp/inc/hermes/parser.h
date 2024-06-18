#pragma once

#include <istream>
#include <memory>

namespace hermes {

template<typename HermesReturn>
class Grammar;

template<typename HermesReturn>
class Parser
{
public:
    Parser(std::shared_ptr<Grammar<HermesReturn>> grammar)
        : grammar(grammar)
    {
    }

    HermesReturn parse(std::shared_ptr<std::istream> input, bool& errored);

private:
    const std::shared_ptr<Grammar<HermesReturn>> grammar;
};

} //namespace hermes