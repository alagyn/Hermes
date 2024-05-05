#pragma once

#include <memory>
#include <vector>

namespace hermes {

using StrType = const std::string&;

class Node
{
public:
    virtual bool match(StrType str, int& pos) = 0;
};

using NodePtr = std::shared_ptr<Node>;

class LiteralNode : public Node
{
public:
    const char sym;

    LiteralNode(char sym);
    bool match(StrType str, int& pos) override;
};

class CharClassNode : public Node
{
public:
    std::vector<char> syms;
    const bool invert;

    CharClassNode(const std::vector<char>& syms, bool invert);
    bool match(StrType str, int& pos) override;
};

// Accepts any char
class DotNode : public Node
{
public:
    DotNode();
    bool match(StrType str, int& pos) override;
};

class ConcatNode : public Node
{
public:
    const NodePtr p1;
    const NodePtr p2;

    ConcatNode(NodePtr p1, NodePtr p2);
    bool match(StrType str, int& pos) override;
};

class AlterationNode : public Node
{
public:
    const NodePtr p1;
    const NodePtr p2;

    AlterationNode(NodePtr p1, NodePtr p2);
    bool match(StrType str, int& pos) override;
};

// star, plus, question, and curly brackets
class RepetitionNode : public Node
{
public:
    const NodePtr p;
    const int min;
    const int max;
    RepetitionNode(NodePtr p, int min, int max);
    bool match(StrType str, int& pos) override;
};

// Parenthesis
class GroupNode : public Node
{
public:
    const NodePtr p;

    GroupNode(NodePtr p);
    bool match(StrType str, int& pos) override;
};

/*
class LineStartNode : public Node
{
public:
    LineStartNode();
    bool match(StrType str, int& pos) override;
};

class LineEndNode : public Node
{
public:
    LineEndNode();
    bool match(StrType str, int& pos) override;
};
*/

} //namespace hermes