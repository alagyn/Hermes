#pragma once

#include <deque>
#include <iostream>
#include <memory>
#include <sstream>

#include <hermes/errors.h>
#include <hermes/parseTable.h>
#include <hermes/scanner.h>
#include <hermes/stackItem.h>

namespace hermes {

// Forward declares
template<typename HermesReturn>
class ParseTable;

template<typename HermesReturn>
class StackToken : public StackItem<HermesReturn>
{
public:
    ParseToken token;

    StackToken(HState state, ParseToken token)
        : StackItem<HermesReturn>(state)
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

    StackNonTerm(HState state, HermesReturn hr)
        : StackItem<HermesReturn>(state)
        , hr(hr)
    {
    }

    static inline std::shared_ptr<StackNonTerm> New(HState state, HermesReturn hr)
    {
        return std::make_shared<StackNonTerm>(state, hr);
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
HermesReturn parse(
    const std::shared_ptr<Scanner> scanner,
    const std::shared_ptr<ParseTable<HermesReturn>> parseTable
)
{
    using StackItemPtr = std::shared_ptr<StackItem<HermesReturn>>;
    std::deque<StackItemPtr> stack;
    // Init by pushing the starting state onto the stack
    stack.push_back(StackToken<HermesReturn>::New(0, ParseToken()));

    ParseToken token = scanner->nextToken();

    while(true)
    {
        ParseAction nextAction =
            parseTable->getAction(stack.back()->state, token.symbol);

#ifdef HERMES_PARSE_DEBUG
        std::cout << "S" << stack.back()->state << " "
                  << parseTable->lookupSymbol(token.symbol)
                  << " Loc:" << token.lineNum << ":" << token.charNum << " '"
                  << token.text << "' ";
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
            auto reduction = parseTable->getReduction(nextAction.state);

#ifdef HERMES_PARSE_DEBUG
            std::cout << "Reduce to \""
                      << parseTable->lookupSymbol(reduction.nonterm) << "\""
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
                HermesReturn hr = parseTable->reduce(nextAction.state, items);

                if(nextAction.state == 0)
                {
                    // Accept
                    return hr;
                }

                ParseAction nextGoto =
                    parseTable->getAction(stack.back()->state, reduction.nonterm);

                stack.push_back(
                    StackNonTerm<HermesReturn>::New(nextGoto.state, hr)
                );
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
               << token.charNum
               << " token: " << parseTable->lookupSymbol(token.symbol)
               << " text:\n'" << token.text << "'\n";
#ifdef HERMES_PARSE_DEBUG
            ss << "Stack: ";

            for(auto& x : stack)
            {
                ss << x->state << " ";
            }
#endif
            ss << "Expected one of: ";
            for(int i = 0; i < parseTable->numCols; ++i)
            {
                HState state = stack.back()->state;
                // Have to offset i here for the start symbol
                auto x = parseTable->getAction(stack.back()->state, i + 1);
                if(x.action == S)
                {
                    ss << parseTable->lookupSymbol(i) << " ";
                }
            }

            ss << "\n";

            throw HermesError(ss.str());
        }
        }
    }
}

} //namespace hermes