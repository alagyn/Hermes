#include <hermes/internal/regex/regex.h>

#include <hermes/errors.h>
#include <hermes/internal/regex/rparser.h>

#include <sstream>

using namespace hermes;

Regex::Regex(const std::string& pattern)
    : Regex(pattern.c_str())
{
}

Regex::Regex(const char* pattern)
    : root(parseRegexPattern(pattern))
{
}

Match Regex::match(const std::string& str) const
{
    return match(str.c_str());
}

Match Regex::match(const char* str) const
{
    int pos = 0;
    if(str[pos] == 0)
    {
        throw HermesError("Regex::match() Cannot match empty string");
    }
    Match out;
    bool fullmatch = root->match(str, out);

    out.match = fullmatch;
    // unset partial if we matched the whole thing
    out.partial = !fullmatch && out.partial;

    return out;
}

std::string Regex::toStr() const
{
    return root->toStr();
}

inline void
addLines(std::vector<std::string>& dest, const std::vector<std::string>& src)
{
    for(const std::string& line : src)
    {
        std::stringstream ss;
        ss << "| " << line;
        dest.push_back(ss.str());
    }
}

std::vector<std::string> _annotate(NodePtr root)
{
    std::vector<std::string> lines;

    {
        auto node = std::dynamic_pointer_cast<AlterationNode>(root);
        if(node)
        {
            lines.push_back("Alternation");
            addLines(lines, _annotate(node->p1));
            addLines(lines, _annotate(node->p2));
            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<ConcatNode>(root);
        if(node)
        {
            lines.push_back("Concat");
            addLines(lines, _annotate(node->p1));
            addLines(lines, _annotate(node->p2));
            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<RepetitionNode>(root);
        if(node)
        {
            std::stringstream ss;
            ss << "Repetition {" << node->min << ", " << node->max << "}";
            lines.push_back(ss.str());
            addLines(lines, _annotate(node->p));
            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<GroupNode>(root);
        if(node)
        {
            lines.push_back("Group");
            addLines(lines, _annotate(node->p));
            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<LookAheadNode>(root);
        if(node)
        {
            std::stringstream ss;
            ss << "LookAhead " << node->negative ? "Negative" : "Positive";
            addLines(lines, _annotate(node->p));
            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<LiteralNode>(root);
        if(node)
        {
            std::stringstream ss;
            ss << "Literal '" << node->sym << "'";
            lines.push_back(ss.str());
            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<CharClassNode>(root);
        if(node)
        {
            std::stringstream ss;
            ss << "CharClass [";
            for(const char& c : node->syms)
            {
                ss << c;
            }

            ss << "]";
            lines.push_back(ss.str());

            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<DotNode>(root);
        if(node)
        {
            lines.push_back("DotNode");

            return lines;
        }
    }

    {
        auto node = std::dynamic_pointer_cast<EndOfStringNode>(root);
        if(node)
        {
            lines.push_back("EndOfString");
            return lines;
        }
    }

    throw HermesError("Invalid node?");
}

std::string Regex::annotate() const
{
    std::stringstream ss;

    auto lines = _annotate(root);

    for(const std::string& line : lines)
    {
        ss << line << std::endl;
    }

    return ss.str();
}
