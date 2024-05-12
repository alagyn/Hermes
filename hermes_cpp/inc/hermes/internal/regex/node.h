#pragma once

#include <memory>
#include <string>
#include <vector>

#include <hermes/internal/regex/match.h>

namespace hermes {

class Node
{
public:
    virtual void match(const char* str, Match& m) = 0;
    virtual std::string toStr() = 0;
};

using NodePtr = std::shared_ptr<Node>;

class LiteralNode : public Node
{
public:
    const char sym;

    LiteralNode(char sym);
    void match(const char* str, Match& m) override;
    std::string toStr() override;
};

class CharClassNode : public Node
{
public:
    std::vector<char> syms;
    bool invert;

    CharClassNode();
    void match(const char* str, Match& m) override;
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

    void match(const char* str, Match& m) override;
    std::string toStr() override;
};

class ConcatNode : public Node
{
public:
    const NodePtr p1;
    const NodePtr p2;

    ConcatNode(NodePtr p1, NodePtr p2);
    void match(const char* str, Match& m) override;
    std::string toStr() override;
};

class AlterationNode : public Node
{
public:
    const NodePtr p1;
    const NodePtr p2;

    AlterationNode(NodePtr p1, NodePtr p2);
    void match(const char* str, Match& m) override;
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
    void match(const char* str, Match& m) override;
    std::string toStr() override;

private:
    void recurse(
        const char* str,
        std::list<int>& out,
        int curPos,
        int curMatch,
        bool& partial
    );
};

// Parenthesis
class GroupNode : public Node
{
public:
    const NodePtr p;

    GroupNode(NodePtr p);
    void match(const char* str, Match& m) override;
    std::string toStr() override;
};

class LookAheadNode : public Node
{
public:
    const NodePtr p;
    const bool negative;

    LookAheadNode(NodePtr p, bool negative);
    void match(const char* str, Match& m) override;
    std::string toStr() override;
};

/*
class LineStartNode : public Node
{
public:
    LineStartNode();
    void match(const char* str, Match& m) override;
};

class LineEndNode : public Node
{
public:
    LineEndNode();
    void match(const char* str, Match& m) override;
};
*/

class EndOfStringNode : public Node
{
public:
    EndOfStringNode()
    {
    }

    void match(const char* str, Match& m) override;
    std::string toStr() override;
};

} //namespace hermes