#pragma once

#include <hermes/regex/regex.h>

#include <map>
#include <string>
#include <vector>

namespace hermes {

// Error
constexpr char E = 0;
// Shift
constexpr char S = 1;
// Reduce
constexpr char R = 2;
// Goto
constexpr char G = 3;

typedef struct
{
    // The number of states to pop
    unsigned short numPops;
    // The ID of the nonterminal reduced to
    unsigned short nonterm;
} Reduction;

typedef struct
{
    char action = E;
    unsigned short state = 0;
} ParseAction;

template<typename HermesReturn>
class StackItem;

template<typename HermesReturn>
class ParseTable
{
    using StackItemPtr = std::shared_ptr<StackItem<HermesReturn>>;
    using ReductionFunc = HermesReturn (*)(std::vector<StackItemPtr>);

public:
    const unsigned numCols;
    const unsigned numRows;

    static std::shared_ptr<ParseTable<HermesReturn>>
    New(const ParseAction* parseTable,
        unsigned numCols,
        unsigned numRows,
        const Reduction* reductions,
        const ReductionFunc* reductionFuncs,
        const std::string* symbolLookup)
    {
        return std::make_shared<ParseTable<HermesReturn>>(
            parseTable,
            numCols,
            numRows,
            reductions,
            reductionFuncs,
            symbolLookup
        );
    }

    ParseTable(
        const ParseAction* parseTable,
        unsigned numCols,
        unsigned numRows,
        const Reduction* reductions,
        const ReductionFunc* reductionFuncs,
        const std::string* symbolLookup
    )
        : numCols(numCols)
        , numRows(numRows)
        , parseTable(parseTable)
        , reductions(reductions)
        , reductionFuncs(reductionFuncs)
        , symbolLookup(symbolLookup)
    {
    }

    inline HermesReturn reduce(
        short rule,
        std::vector<std::shared_ptr<StackItem<HermesReturn>>>& items
    ) const
    {
        return reductionFuncs[rule](items);
    }

    inline const std::string& lookupSymbol(unsigned symbol) const
    {
        return symbolLookup[symbol];
    }

    inline const Reduction& getReduction(short rule) const
    {
        return reductions[rule];
    }

    inline const ParseAction& getAction(unsigned state, unsigned symbol) const
    {
        return parseTable[(state * numCols) + (symbol - 1)];
    }

private:
    const ParseAction* parseTable;
    const Reduction* reductions;
    const ReductionFunc* reductionFuncs;
    const std::string* symbolLookup;
};

} //namespace hermes
