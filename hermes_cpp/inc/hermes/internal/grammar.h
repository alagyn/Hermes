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

    StackItem(HState state, unsigned symbol)
        : state(state)
        , symbol(symbol)
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
        : StackItem<HermesReturn>(state, token.symbol)
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

    StackNonTerm(HState state, unsigned symbol, HermesReturn hr)
        : StackItem<HermesReturn>(state, symbol)
        , hr(hr)
    {
    }

    static inline std::shared_ptr<StackNonTerm>
    New(HState state, unsigned symbol, HermesReturn hr)
    {
        return std::make_shared<StackNonTerm>(state, symbol, hr);
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
        unsigned symbolEOF,
        unsigned symbolIGNORE)
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
            symbolEOF,
            symbolIGNORE
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
        unsigned symbolEOF,
        unsigned symbolIGNORE
    )
        : parseTable(parseTable)
        , numCols(numCols)
        , numRows(numRows)
        , reductions(reductions)
        , reductionFuncs(reductionFuncs)
        , symbolLookup(symbolLookup)
        , terminals()
        , symbolEOF(symbolEOF)
        , symbolIGNORE(symbolIGNORE)
    {
        terminals.reserve(numTerminals);
        for(size_t i = 0; i < numTerminals; ++i)
        {
            const TerminalDef& def = terminalDefs[i];
            terminals.push_back({def.id, hermes::Regex(def.str)});
        }
    }

    HermesReturn parse(std::shared_ptr<Scanner> scanner)
    {
        std::deque<StackItemPtr> stack;
        // Init by pushing the starting state onto the stack
        stack.push_back(StackToken<HermesReturn>::New(0, ParseToken()));

        ParseToken token = scanner->nextToken();

        while(true)
        {
            ParseAction nextAction =
                getAction(stack.back()->state, token.symbol);

#ifdef HERMES_PARSE_DEBUG
            std::cout << "S" << stack.back()->state << " "
                      << lookupSymbol(token.symbol) << " Loc:" << token.lineNum
                      << ":" << token.charNum << " '" << token.text << "' ";
#endif

            switch(nextAction.action)
            {
            case S:
            {
#ifdef HERMES_PARSE_DEBUG
                std::cout << "S" << nextAction.state << "\n";
#endif
                stack.push_back(
                    StackToken<HermesReturn>::New(nextAction.state, token)
                );
                // We only get the next token after a shift
                token = scanner->nextToken();

                break;
            }
            case R:
            {
                auto reduction = getReduction(nextAction.state);

#ifdef HERMES_PARSE_DEBUG
                std::cout << "Reduce to \"" << lookupSymbol(reduction.nonterm)
                          << "\""
                          << " via rule: " << nextAction.state << " {"
                          << " pops: " << reduction.numPops << " goto idx: "
                          << static_cast<unsigned>(reduction.nonterm) << " }\n";
#endif
                std::vector<StackItemPtr> items;
                for(int i = 0; i < reduction.numPops; ++i)
                {
                    items.push_back(stack.back());
                    stack.pop_back();
                }

                try
                {
                    HermesReturn hr = reduce(nextAction.state, items);

                    if(nextAction.state == 0)
                    {
                        // Accept
                        return hr;
                    }

                    ParseAction nextGoto =
                        getAction(stack.back()->state, reduction.nonterm);

                    stack.push_back(StackNonTerm<HermesReturn>::New(
                        nextGoto.state,
                        reduction.nonterm,
                        hr
                    ));
                }
                catch(const std::exception& err)
                {
                    std::stringstream ss;
                    ss << "Reduce Error at " << token.lineNum << ":"
                       << token.charNum << " token: " << token.text;
                    ss << "\nThis token may/or may not be the issue\nError:\n"
                       << err.what();
                    throw HermesError(ss.str());
                }
                break;
            }
            default:
            {
                // TODO convert to an exception?
                std::cout << "\n";
                std::stringstream ss;
                ss << "Parse Error at line " << token.lineNum << " char "
                   << token.charNum << " token: " << lookupSymbol(token.symbol)
                   << " text:\n'" << token.text << "'\n";
#ifdef HERMES_PARSE_DEBUG
                ss << "Stack: ";

                for(auto& x : stack)
                {
                    ss << symbolLookup[x->symbol] << " ";
                }

#endif
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

                throw HermesError(ss.str());
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
HermesReturn Parser<HermesReturn>::parse(std::shared_ptr<std::istream> input)
{
    auto scanner = Scanner::New(
        input,
        grammar->terminals.data(),
        grammar->terminals.size(),
        grammar->symbolEOF,
        grammar->symbolIGNORE
    );
    return grammar->parse(scanner);
}

} //namespace hermes