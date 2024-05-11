#pragma once

#include <memory>
#include <string>
#include <vector>

#include <hermes/internal/regex/match.h>

namespace hermes {

class Node
{
public:
    virtual bool match(const char* str, Match& m) = 0;
    virtual std::string toStr() = 0;
};

using NodePtr = std::shared_ptr<Node>;

class LiteralNode : public Node
{
public:
    const char sym;

    LiteralNode(char sym);
    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

class CharClassNode : public Node
{
public:
    std::vector<char> syms;
    bool invert;

    CharClassNode();
    bool match(const char* str, Match& m) override;
    void pushRange(char s, char e);
    std::string toStr() override;
};

// Accepts any char
class DotNode : public Node
{
public:
    DotNode()
    {
    }

    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

class ConcatNode : public Node
{
public:
    const NodePtr p1;
    const NodePtr p2;

    ConcatNode(NodePtr p1, NodePtr p2);
    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

class AlterationNode : public Node
{
public:
    const NodePtr p1;
    const NodePtr p2;

    AlterationNode(NodePtr p1, NodePtr p2);
    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

// star, plus, question, and curly brackets
class RepetitionNode : public Node
{
public:
    const NodePtr p;
    const int min;
    const int max;
    RepetitionNode(NodePtr p, int min, int max);
    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

// Parenthesis
class GroupNode : public Node
{
public:
    const NodePtr p;

    GroupNode(NodePtr p);
    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

class LookAheadNode : public Node
{
public:
    const NodePtr p;
    const bool negative;

    LookAheadNode(NodePtr p, bool negative);
    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

/*
class LineStartNode : public Node
{
public:
    LineStartNode();
    bool match(const char* str, Match& m) override;
};

class LineEndNode : public Node
{
public:
    LineEndNode();
    bool match(const char* str, Match& m) override;
};
*/

class EndOfStringNode : public Node
{
public:
    EndOfStringNode()
    {
    }

    bool match(const char* str, Match& m) override;
    std::string toStr() override;
};

} //namespace hermes