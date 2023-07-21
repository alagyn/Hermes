#include <hermes/errors.h>
#include <hermes/parseTable.h>
#include <hermes/parser.h>

#include <iostream>
#include <sstream>

namespace hermes {

class StackItem
{
public:
    HState state;

    StackItem(HState state)
        : state(state)
    {
    }

    virtual std::string t() = 0;
    virtual HERMES_RETURN nt() = 0;
};

class StackToken : public StackItem
{
public:
    ParseToken token;

    StackToken(HState state, ParseToken token)
        : StackItem(state)
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

    HERMES_RETURN nt() override
    {
        throw HermesError("StackToken::nt() This ain't a nonterminal, son");
    }
};

class StackNonTerm : public StackItem
{
public:
    HERMES_RETURN hr;

    StackNonTerm(HState state, HERMES_RETURN hr)
        : StackItem(state)
        , hr(hr)
    {
    }

    static inline std::shared_ptr<StackNonTerm>
    New(HState state, HERMES_RETURN hr)
    {
        return std::make_shared<StackNonTerm>(state, hr);
    }

    std::string t() override
    {
        throw HermesError("StackToken::nt() This ain't a terminal, son");
    }

    HERMES_RETURN nt() override
    {
        return hr;
    }
};

HERMES_RETURN Parser::parse(std::shared_ptr<Scanner> scanner)
{
    stack.clear();
    // Init by pushing the starting state onto the stack
    stack.push_back(StackToken::New(0, ParseToken()));

    ParseToken token = scanner->nextToken();

    while(true)
    {
        ParseAction nextAction = getAction(stack.back()->state, token.symbol);

        std::cout << symbolLookup(token.symbol) << " " << token.lineNum << "."
                  << token.charNum << " " << token.text << " ";

        switch(nextAction.action)
        {
        case S:
        {
            std::cout << "S" << nextAction.state << "\n";
            stack.push_back(StackToken::New(nextAction.state, token));
            // We only get the next token after a shift
            token = scanner->nextToken();
            break;
        }
        case R:
        {
            if(nextAction.state == 0)
            {
                std::cout << "Reduce to ACCEPT\n";
                // TODO ACCEPT
                return nullptr;
            }

            auto reduction = getReduction(nextAction.state);
            std::cout << "Reduce to \"" << symbolLookup(reduction.nonterm)
                      << "\""
                      << " via rule: " << nextAction.state << " {"
                      << " pops: " << reduction.numPops << " goto idx: "
                      << static_cast<unsigned>(reduction.nonterm) << " }\n";

            std::vector<StackItemPtr> items;
            for(int i = 0; i < reduction.numPops; ++i)
            {
                items.push_back(stack.back());
                stack.pop_back();
            }

            HERMES_RETURN hr = reduce(nextAction.state, items);

            ParseAction nextGoto =
                getAction(stack.back()->state, reduction.nonterm);

            stack.push_back(StackNonTerm::New(nextGoto.state, hr));

            break;
        }
        default:
        {
            std::cout << "\n";
            std::stringstream ss;
            ss << "Parse Error at line " << token.lineNum << " char "
               << token.charNum << " token: " << token.text << "\n";
            ss << "Stack: ";
            for(auto& x : stack)
            {
                ss << x->state << " ";
            }

            ss << "Expected one of: ";
            for(int i = 0; i < numCols(); ++i)
            {
                auto x = getAction(stack.back()->state, i);
                if(x.action != E)
                {
                    ss << symbolLookup(i) << " ";
                }
            }

            ss << "\n";

            throw std::runtime_error(ss.str());
        }
        }
    }
}

} //namespace hermes