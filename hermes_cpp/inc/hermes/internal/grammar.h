#pragma once

#include <deque>
#include <iostream>
#include <memory>
#include <sstream>
#include <vector>

#include <hermes/errors.h>
#include <hermes/internal/scanner.h>
#include <hermes/parser.h>

namespace hermes {

// hold regex strs so we can instantiate them when
// the grammar gets loaded
typedef struct
{
    unsigned id;
    const char* str;
} TerminalDef;

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

typedef unsigned HState;

template<typename HermesReturn>
class StackItem
{
public:
    HState state;
    unsigned symbol;
    Location loc;

    StackItem(HState state, unsigned symbol, Location loc)
        : state(state)
        , symbol(symbol)
        , loc(loc)
    {
    }

    virtual std::string t() = 0;
    virtual HermesReturn nt() = 0;
};

template<typename HermesReturn>
class StackToken : public StackItem<HermesReturn>
{
public:
    ParseToken token;

    StackToken(HState state, ParseToken token)
        : StackItem<HermesReturn>(state, token.symbol, token.loc)
        , token(token)
    {
    }

    static inline std::shared_ptr<StackToken> New(HState state, ParseToken token)
    {
        return std::make_shared<StackToken>(state, token);
    }

    std::string t() override
    {
        return token.text;
    }

    HermesReturn nt() override
    {
        throw HermesError("StackToken::nt() This ain't a nonterminal, son");
    }
};

template<typename HermesReturn>
class StackNonTerm : public StackItem<HermesReturn>
{
public:
    HermesReturn hr;

    StackNonTerm(HState state, unsigned symbol, HermesReturn hr, Location loc)
        : StackItem<HermesReturn>(state, symbol, loc)
        , hr(hr)
    {
    }

    static inline std::shared_ptr<StackNonTerm>
    New(const HState state,
        const unsigned symbol,
        const HermesReturn hr,
        const Location loc)
    {
        return std::make_shared<StackNonTerm>(state, symbol, hr, loc);
    }

    std::string t() override
    {
        throw HermesError("StackToken::nt() This ain't a terminal, son");
    }

    HermesReturn nt() override
    {
        return hr;
    }
};

template<typename HermesReturn>
class Grammar
{
public:
    using StackItemPtr = std::shared_ptr<StackItem<HermesReturn>>;
    using ReductionFunc = HermesReturn (*)(std::vector<StackItemPtr>);

    const ParseAction* parseTable;
    const unsigned numCols;
    const unsigned numRows;

    const Reduction* reductions;
    const ReductionFunc* reductionFuncs;

    const std::string* symbolLookup;

    const size_t numSymbols;

    const unsigned symbolERROR;
    const unsigned symbolEOF;
    const unsigned symbolIGNORE;

    std::vector<Terminal> terminals;

    static std::shared_ptr<Grammar<HermesReturn>>
    New(const ParseAction* parseTable,
        unsigned numCols,
        unsigned numRows,
        const Reduction* reductions,
        const ReductionFunc* reductionFuncs,
        const std::string* symbolLookup,
        const TerminalDef* terminalDefs,
        size_t numTerminals,
        size_t numSymbols)
    {
        return std::make_shared<Grammar<HermesReturn>>(
            parseTable,
            numCols,
            numRows,
            reductions,
            reductionFuncs,
            symbolLookup,
            terminalDefs,
            numTerminals,
            numSymbols
        );
    }

    Grammar(
        const ParseAction* parseTable,
        unsigned numCols,
        unsigned numRows,
        const Reduction* reductions,
        const ReductionFunc* reductionFuncs,
        const std::string* symbolLookup,
        const TerminalDef* terminalDefs,
        size_t numTerminals,
        size_t numSymbols
    )
        : parseTable(parseTable)
        , numCols(numCols)
        , numRows(numRows)
        , reductions(reductions)
        , reductionFuncs(reductionFuncs)
        , symbolLookup(symbolLookup)
        , numSymbols(numSymbols)
        , terminals()
        , symbolERROR(numSymbols - 3)
        , symbolEOF(numSymbols - 2)
        , symbolIGNORE(numSymbols - 1)
    {
        terminals.reserve(numTerminals);
        for(size_t i = 0; i < numTerminals; ++i)
        {
            const TerminalDef& def = terminalDefs[i];
            terminals.push_back({def.id, hermes::Regex(def.str)});
        }
    }

    HermesReturn parse(std::shared_ptr<Scanner> scanner, bool& errored)
    {
        std::deque<StackItemPtr> stack;
        // Init by pushing the starting state onto the stack
        stack.push_back(StackToken<HermesReturn>::New(0, ParseToken()));

        ParseToken token = scanner->nextToken();
        errored = false;
        bool errorRecovery = false;
        ParseToken errorToken;

        while(true)
        {
            ParseAction nextAction =
                getAction(stack.back()->state, token.symbol);

#ifdef HERMES_PARSE_DEBUG
            std::cout << "State:" << stack.back()->state
                      << " Token: " << lookupSymbol(token.symbol)
                      << " Loc:" << token.loc.lineStart << ":"
                      << token.loc.charStart << " Text: '" << token.text
                      << "'\n\t↳ ";
#endif

            switch(nextAction.action)
            {
            case S:
            {
                stack.push_back(
                    StackToken<HermesReturn>::New(nextAction.state, token)
                );
#ifdef HERMES_PARSE_DEBUG
                std::cout << "Shift to state " << nextAction.state << "\n";
#endif
                // We only get the next token after a shift
                token = scanner->nextToken();

                break;
            }
            case R:
            {
                auto reduction = getReduction(nextAction.state);
                std::vector<StackItemPtr> items(reduction.numPops);
                for(int i = 0; i < reduction.numPops; ++i)
                {
                    items[i] = stack.back();
                    if(errorRecovery && items[i]->symbol == symbolERROR)
                    {
                        errorRecovery = false;
                    }
                    stack.pop_back();
                }

#ifdef HERMES_PARSE_DEBUG
                std::cout << "Reduce to \"" << lookupSymbol(reduction.nonterm)
                          << "\""
                          << " via rule: " << nextAction.state << " popping "
                          << reduction.numPops << " items and goto state "
                          << stack.back()->state << "\n";
#endif

                HermesReturn hr = reduce(nextAction.state, items);

                if(nextAction.state == 0)
                {
#ifdef HERMES_PARSE_DEBUG
                    std::cout << "Input Accepted";
                    if(errored)
                    {
                        std::cout << ", but Syntax Error Occurred";
                    }
                    std::cout << '\n';
#endif

                    // Accept
                    return hr;
                }

                ParseAction nextGoto =
                    getAction(stack.back()->state, reduction.nonterm);

                Location nextLoc;
                if(!items.empty())
                {
                    nextLoc.lineStart = items[0]->loc.lineStart;
                    nextLoc.charStart = items[0]->loc.charStart;
                    nextLoc.lineEnd = items[items.size() - 1]->loc.lineEnd;
                    nextLoc.lineEnd = items[items.size() - 1]->loc.lineEnd;
                }
                else
                {
                    nextLoc = stack.back()->loc;
                }

                stack.push_back(StackNonTerm<HermesReturn>::New(
                    nextGoto.state,
                    reduction.nonterm,
                    hr,
                    nextLoc
                ));
                break;
            }
            default:
            {
                // Error

                // If we are already in error recovery, just skip the token
                if(errorRecovery)
                {
#ifdef HERMES_PARSE_DEBUG
                    std::cout << "Error recovery: skipping unusable token "
                              << lookupSymbol(token.symbol) << '\n';
#endif
                    token = scanner->nextToken();
                    /*
                    if(token.symbol == symbolEOF)
                    {
                        std::stringstream ss;
                        ss << "Fatal Error: invalid token at line "
                           << errorToken.loc.lineStart << ":"
                           << errorToken.loc.charStart
                           << " Token: " << lookupSymbol(token.symbol)
                           << " Text: '" << errorToken.text << "'"
                           << " Hit EOF during error recovery";
                        throw HermesError(ss.str());
                    }
                    */
                }
                else
                {
#ifdef HERMES_PARSE_DEBUG
                    std::cout << "Invalid token Loc:" << token.loc.lineStart
                              << ":" << token.loc.charStart
                              << " attempting to find error state\n";
                    std::cout << "\tStack: ";
                    for(auto& x : stack)
                    {
                        std::cout << symbolLookup[x->symbol] << " ";
                    }
                    std::cout << '\n';
                    std::deque<StackItemPtr> debugStack;
#endif
                    errorToken = token;

                    // Discard stack items until we find a state that can shift on ERROR
                    while(true)
                    {
                        nextAction = getAction(stack.back()->state, symbolERROR);
                        if(nextAction.action == S)
                        {
                            break;
                        }

#ifdef HERMES_PARSE_DEBUG
                        std::cout << "\tPopping stack item state: "
                                  << stack.back()->state << " symbol: "
                                  << symbolLookup[stack.back()->symbol] << '\n';
                        debugStack.push_front(stack.back());
#endif

                        stack.pop_back();
                        if(stack.empty())
                        {
                            std::stringstream ss;
                            ss << "Fatal Error: invalid token at line "
                               << errorToken.loc.lineStart << ":"
                               << errorToken.loc.charStart
                               << " Token: " << lookupSymbol(errorToken.symbol)
                               << " Text: '" << errorToken.text << "'";
#ifdef HERMES_PARSE_DEBUG
                            ss << "\nStack: ";
                            for(auto& x : debugStack)
                            {
                                ss << symbolLookup[x->symbol] << " ";
                            }
                            ss << '\n';

                            ss << "Expected one of: ";
                            for(int i = 0; i < numCols; ++i)
                            {
                                HState state = stack.back()->state;
                                // Have to offset i here for the start symbol
                                auto x = getAction(stack.back()->state, i + 1);
                                if(x.action == S)
                                {
                                    ss << lookupSymbol(i) << " ";
                                }
                            }

                            ss << "\n";
#endif
                            throw HermesError(ss.str());
                        }
                    } // End while stack

#ifdef HERMES_PARSE_DEBUG
                    std::cout << "\tFound Error shift in state "
                              << stack.back()->state << " -> state "
                              << nextAction.state << "\n";
#endif

                    // If we got here we found a state where we can shift on
                    // ERROR do the shift
                    token.symbol = symbolERROR;

                    /*
                    ParseToken temp = errorToken;
                    temp.symbol = symbolERROR;
                    temp.text = "ERROR";
                    stack.push_back(
                        StackToken<HermesReturn>::New(nextAction.state, temp)
                    );

                    token = scanner->nextToken();
                    */
                    // Then loop and try to continue parsing until we reduce and
                    // pop the error symbol off the stack
                    errored = true;
                    errorRecovery = true;
                }
            }
            }
        }
    }

private:
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
};

// put this template def here so it gets instantiated when needed
template<typename HermesReturn>
HermesReturn
Parser<HermesReturn>::parse(std::shared_ptr<std::istream> input, bool& errored)
{
    auto scanner = Scanner::New(
        input,
        grammar->terminals.data(),
        grammar->terminals.size(),
        grammar->numSymbols
    );
    return grammar->parse(scanner, errored);
}

} //namespace hermes