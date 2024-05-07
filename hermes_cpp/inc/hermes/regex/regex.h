#pragma once

#include <hermes/regex/match.h>

#include <memory>
#include <string>

namespace hermes {

class Node;

class Regex
{
public:
    explicit Regex(const std::string& pattern);
    explicit Regex(const char* pattern);

    Match match(const std::string& str) const;
    Match match(const char* str) const;

    std::string toStr() const;

private:
    std::shared_ptr<Node> root;
};

} //namespace hermes