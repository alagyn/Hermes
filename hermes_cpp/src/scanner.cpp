#include <hermes/scanner.h>

#include <iostream>
#include <list>
#include <sstream>

#include <boost/regex.h>

#include <hermes/parseTable.h>

using namespace std;

namespace hermes {
Scanner::Scanner(string filename)
    : handle(filename)
    , curLineNum(1)
    , curCharNum(0)
{
}

Scanner::~Scanner()
{
    if(handle.is_open())
    {
        handle.close();
    }
}

void Scanner::consumeNewLine(char& nextChar)
{
    // Handle windows/mac line endings
    if(nextChar == '\r')
    {
        nextChar = handle.get();
        if(nextChar != '\n')
        {
            // If it wasn't actually \r\n, unget
            handle.unget();
            // Force to \n to for next if block
            nextChar = '\n';
        }
    }
}

ParseToken Scanner::nextToken()
{
    ParseToken out;
    out.lineNum = curLineNum;
    out.charNum = curCharNum;

    if(handle.eof())
    {
        out.symbol = eofSymbol();
        return out;
    }

    // TODO optimizations here
    /*
        we can maybe keep track of whether each terminal has starting
       matching yet and prune when they stop. This will cause errors if the
       re has to ability to go in and out of matching, but is that a common
       thing for the kinds of re here?

       this may be overkill as there is a rather low number of regexs to check
    */

    // flag for if we have started having matches
    bool foundMatch = false;
    while(!handle.eof())
    {
        char nextChar;
        handle.get(nextChar);
        if(handle.eof())
        {
            // If we are at EOF and we have found a match
            if(foundMatch)
            {
                for(auto& x : getTerminals())
                {
                    if(boost::regex_match(out.text, x.re))
                    {
                        // Take the first that matches
                        out.symbol = x.id;
                    }
                }
                return out;
            }
            else
            {
                break;
            }
        }
        ++curCharNum;
        ++out.charNum;

        // Preprocess comments
        if(nextChar == '#')
        {
            nextChar = handle.get();
            // Handle multiline comments
            if(nextChar == '#')
            {
                while(true)
                {
                    do
                    {
                        nextChar = handle.get();
                    }
                    while(nextChar != '#');
                    nextChar = handle.get();
                    if(nextChar == '#')
                    {
                        break;
                    }
                }
            }
            // Handle line comments
            else
            {
                do
                {
                    nextChar = handle.get();
                }
                while(nextChar != '\r' && nextChar != '\n');
                consumeNewLine(nextChar);
            }

            continue;
        }

        consumeNewLine(nextChar);

        if(nextChar == ' ' || nextChar == '\t' || nextChar == '\n')
        {
            // Ignore leading whitespace
            // We can't ignore all whitespace otherwise we break strings
            if(!out.text.empty())
            {
                out.text.push_back(nextChar);
            }
        }
        else
        {
            out.text.push_back(nextChar);
        }

        bool foundNewMatch = false;
        for(auto& t : getTerminals())
        {
            if(boost::regex_match(out.text, t.re))
            {
                foundNewMatch = true;
                // Short circuit. We only need to see if a single one matches
                break;
            }
        }

        if(nextChar == '\n')
        {
            ++curLineNum;
            ++out.lineNum;
            curCharNum = 0;
        }

        // If we haven't gotten a match yet and we just found a new one
        if(!foundMatch && foundNewMatch)
        {
            // Set foundMatch to true
            foundMatch = true;
        }
        // Else if we previously found a match and then stopped or we hit whitespace
        else if(foundMatch && !foundNewMatch)
        {
            // Therefore we have found the maximal-munch
            // We need to unget the last char so we don't consume it
            // we already skip whitespace
            handle.unget();
            out.text.pop_back();

            /*
                Find the first terminal that matches
            */
            for(auto& term : getTerminals())
            {
                if(boost::regex_match(out.text, term.re))
                {
                    out.symbol = term.id;
                    return out;
                }
            }

            // If we got here something bad happened and nothing matched
            std::stringstream ss;
            ss << "Bad token: '" << out.text << "'";
            throw std::runtime_error(ss.str());
        }
    }

    // We only got here if there was an EOF
    // Return EOF which will error later?
    // TODO make sure this is the case?
    out.symbol = eofSymbol();
    return out;
};
} //namespace hermes