#include <hermes/parseTable.h>
#include <hermes/symbol.h>

#include <hermes/_parseTable.h>

namespace hermes {

// Symbol Lookup
const std::string& symbolLookup(Symbol symbol)
{
    return symbolLookup(static_cast<unsigned>(symbol));
}

const std::string& symbolLookup(unsigned symbol)
{
    return SYMBOL_LOOKUP.at(symbol);
}

// Get Action
const ParseAction& getAction(unsigned state, Symbol symbol)
{
    return getAction(state, static_cast<unsigned>(symbol));
}

const ParseAction& getAction(unsigned state, unsigned symbol)
{
    return PARSE_TABLE[state][symbol];
}

// Get Terminals
const std::vector<Terminal>& getTerminals()
{
    return TERMINALS;
}

const Terminal& getTerminal(Symbol symbol)
{
    return TERMINALS.at(static_cast<unsigned>(symbol));
}

// Get Reduction
const Reduction& getReduction(short rule)
{
    return REDUCTIONS.at(rule);
}

HERMES_RETURN reduce(short rule, std::vector<std::shared_ptr<StackItem>>& items)
{
    return reductionFuncs.at(rule)(items);
}

const unsigned numRows()
{
    return TABLE_ROWS;
}

const unsigned numCols()
{
    return TABLE_COLS;
}

} //namespace hermes