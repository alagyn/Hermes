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

    bool match(const char* str);

private:
    std::shared_ptr<Node> root;
};

} //namespace hermes