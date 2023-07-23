#include <hermes/scanner.h>

#include <iostream>
#include <list>
#include <sstream>

#include <boost/regex.h>

#include <hermes/errors.h>
#include <hermes/parseTable.h>

using namespace std;

namespace hermes {

std::shared_ptr<Scanner> Scanner::New(std::shared_ptr<std::istream> handle)
{
    return std::make_shared<Scanner>(handle);
}

char Scanner::get()
{
    char out = handle->get();
    // Handle windows/mac line endings
    if(out == '\r')
    {
        out = handle->get();
        if(out != '\n')
        {
            // If it wasn't actually \r\n, unget
            handle->unget();
            // Force to \n to for next if block
            out = '\n';
        }
    }

    if(out == '\n')
    {
        ++lineNum;
        lastLineLength = charNum;
        charNum = 0;
    }
    else
    {
        ++charNum;
    }

    return out;
}

void Scanner::unget()
{
    handle->unget();
    if(handle->peek() == '\n')
    {
        --lineNum;
        charNum = lastLineLength;
    }
    else
    {
        --charNum;
    }
}

Scanner::Scanner(std::shared_ptr<std::istream> handle)
    : handle(handle)
    , lineNum(1)
    , charNum(0)
    , lastLineLength(0)
{
}

ParseToken Scanner::nextToken()
{
    ParseToken out;
    out.lineNum = lineNum;
    out.charNum = charNum;

    if(handle->eof())
    {
        out.symbol = Symbol::__EOF__;
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
    while(!handle->eof())
    {
        char nextChar;
        handle->get(nextChar);
        if(handle->eof())
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

        // Preprocess comments
        if(nextChar == '#')
        {
            nextChar = handle->get();
            // Handle multiline comments
            if(nextChar == '#')
            {
                while(true)
                {
                    do
                    {
                        nextChar = handle->get();
                    }
                    while(nextChar != '#');
                    nextChar = handle->get();
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
                    nextChar = handle->get();
                }
                while(nextChar != '\n');
            }

            continue;
        }

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
            handle->unget();
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
            ss << "Bad token: " << out.lineNum << ":" << out.charNum << "'"
               << out.text << " '";
            throw HermesError(ss.str());
        }
    }

    // We only got here if we hit EOF and didn't have a match
    std::stringstream ss;
    ss << "Bad token: " << out.lineNum << ":" << out.charNum << " '" << out.text
       << "'";
    throw HermesError(ss.str());
};
} //namespace hermes