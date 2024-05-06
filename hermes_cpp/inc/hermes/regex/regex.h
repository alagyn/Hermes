#pragma once

#include <memory>
#include <string>

namespace hermes {

class Node;

class Regex
{
public:
    explicit Regex(const std::string& pattern);
    explicit Regex(const char* pattern);

    bool match(const std::string& str) const;
    bool match(const char* str) const;
    bool match(const std::string& str, bool& partial) const;
    bool match(const char* str, bool& partial) const;

    std::string toStr() const;

private:
    std::shared_ptr<Node> root;
};

} //namespace hermes