#pragma once

#include <hermes/_defaults.h>

#include <map>
#include <string>
#include <vector>

#include <boost/regex.hpp>

namespace hermes {

// Error
constexpr char E = 0;
// Shift
constexpr char S = 1;
// Reduce
constexpr char R = 2;
// Goto
constexpr char G = 3;

enum class Symbol;

const std::string& symbolLookup(unsigned symbol);
const std::string& symbolLookup(Symbol symbol);

typedef struct
{
    Symbol id;
    boost::regex re;
} Terminal;

const Terminal& getTerminal(Symbol symbol);
const std::vector<Terminal>& getTerminals();

typedef struct
{
    // The number of states to pop
    unsigned short numPops;
    // The ID of the nonterminal reduced to
    unsigned short nonterm;
} Reduction;

const Reduction& getReduction(short rule);

const unsigned numRows();
const unsigned numCols();

typedef struct
{
    char action = E;
    unsigned short state = 0;
} ParseAction;

const ParseAction& getAction(unsigned state, unsigned symbol);
const ParseAction& getAction(unsigned state, Symbol symbol);

Symbol eofSymbol();

class StackItem;
HERMES_RETURN reduce(short rule, std::vector<std::shared_ptr<StackItem>>& items);

} //namespace hermes
