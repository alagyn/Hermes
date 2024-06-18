from typing import Dict, List, Tuple, Optional, Set
from collections import deque
import itertools

from hermes_gen.grammar import Grammar, Rule, Symbol
from hermes_gen.errors import HermesError
# TODO condense symbol strings to int IDs


class AnnotRule:
    """
    A rule combined with a parse index and a look ahead
    """

    def __init__(self, rule: Rule, parseIndex: int, lookAhead: set[Symbol]) -> None:
        """
        :param rule: The Rule
        :param parseIndex: The index of the symbol AFTER the dot, i.e. the symbol we are looking for
        :param lookAhead: The look ahead set for the rule
        """
        self.rule = rule
        self.parseIndex = parseIndex
        self.lookAhead = lookAhead

    def __str__(self) -> str:
        out = f'[ {self.strRule()} ]'
        return out

    def __repr__(self) -> str:
        return str(self)

    def strRule(self) -> str:
        out = f'{self.rule.nonterm} ='

        for i in range(self.parseIndex):
            out += " " + str(self.rule.symbols[i])

        out += " •"

        for i in range(self.parseIndex, len(self.rule.symbols)):
            out += " " + str(self.rule.symbols[i])

        return out

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AnnotRule):
            return False

        return self.canCombine(other) and self.lookAhead == other.lookAhead

    def canCombine(self, other: 'AnnotRule'):
        """
        Checks if the rule can be combined with another
        Chcks equality of the underlying rule and the parse index
        """

        return self.rule == other.rule and self.parseIndex == other.parseIndex

    def combine(self, other: 'AnnotRule') -> bool:
        """
        Adds the look ahead of the other rule.
        :param other: The rule to combine
        :return: True if look ahead was changed
        """
        new = self.lookAhead.union(other.lookAhead)
        if new > self.lookAhead:
            self.lookAhead = new
            return True
        return False

    def indexAtEnd(self) -> bool:
        """
        Check if the dot is just before the last symbol
        """
        return self.parseIndex == len(self.rule.symbols)

    def nextSymbol(self) -> Symbol:
        """
        Get the next symbol
        """
        return self.rule.symbols[self.parseIndex]

    def getNewLA(self) -> set[Symbol]:
        """
        Returns the lookahead for closure rules generated from this rule
        Uses set of symbols that can be collapsed after the next symbol to be
        consumed (i.e. every symbol from idx + 1 up to and including
        the first that can't be null)
        :return: The lookahead
        """

        out = set()
        for i in range(self.parseIndex + 1, len(self.rule.symbols)):
            symbol = self.rule.symbols[i]
            out.update(symbol.first - {Symbol.EMPTY})
            if not symbol.nullable:
                return out

        # If we got here, every symbol after the next can be nulled
        # Add our own look ahead
        out.update(self.lookAhead)
        return out

    def __hash__(self) -> int:
        return hash(self.rule.id) + hash(self.parseIndex)

    def __getitem__(self, idx: int) -> Symbol:
        return self.rule.symbols[idx]

    def __len__(self) -> int:
        return len(self.rule.symbols)


class Node:

    def __init__(self, id: int) -> None:
        self.id = id
        self.rules: List[AnnotRule] = []
        # Map of transitions
        self.trans: Dict[Symbol, Node] = {}

    def __str__(self) -> str:
        return f'Node#{self.id}'

    def __repr__(self) -> str:
        return self.__str__()

    def addRule(self, rule: Rule, parseIndex: int, lookAhead: set[Symbol]) -> bool:
        """
        Attempts to add a rule to the node. If a duplicate is found,
        the new LA is merged into the existing rule.
        :param rule: The rule to add
        :param parseIndex: The idx of the next symbol
        :param lookAhead: The new LA
        :return: True if a change occurs
        """
        newRule = AnnotRule(rule, parseIndex, lookAhead)
        for annotRule in self.rules:
            if annotRule.canCombine(newRule):
                return annotRule.combine(newRule)

        self.rules.append(newRule)
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False

        if len(self.rules) != len(other.rules):
            return False

        for r1, r2 in zip(self.rules, other.rules):
            if r1 != r2:
                return False

        return True

    def canCombine(self, other: 'Node') -> bool:
        if len(self.rules) != len(other.rules):
            return False

        for r1, r2 in zip(self.rules, other.rules):
            if not r1.canCombine(r2):
                return False

        return True

    def combine(self, other: 'Node') -> bool:
        out = False
        for ar1, ar2 in zip(self.rules, other.rules):
            if ar1.combine(ar2):
                out = True

        return out

    def addTrans(self, nt: Symbol, node: 'Node'):
        if nt in self.trans:
            raise HermesError(
                f"LALR: Node: {str(self)}\n"
                f"Attempted to add duplicate transition on NT: {nt}\n"
                f"Existing: {str(self.trans[nt])}\n"
                f"New: {str(node)}"
            )

        self.trans[nt] = node

    def __hash__(self) -> int:
        return hash(self.id)


class LALR1Automata:

    def __init__(self, g: Grammar) -> None:
        # Start node is ID 0
        self.start = Node(0)
        # start IDs at 1
        self.nodeIDs = 1

        self.grammar = g

        # Lookup rules for each nonterminal
        self.ruleLookup: Dict[Symbol, List[Rule]] = {}
        for rule in g.rules:
            try:
                self.ruleLookup[rule.nonterm].append(rule)
            except KeyError:
                self.ruleLookup[rule.nonterm] = [rule]

        # Add all the rules for the start symbol to the start node
        for rule in self.ruleLookup[g.startSymbol]:
            self.start.addRule(rule, 0, {Symbol.END})

        # Make the closure for the start node
        self.makeClosure(self.start)

        self.nodes: List[Node] = [self.start]

        # Make the todo queue
        todo = deque([self.start])

        while len(todo) > 0:
            cur = todo.popleft()
            used = set()
            for rule in cur.rules:
                if not rule.indexAtEnd():
                    symbol = rule.nextSymbol()
                    if symbol not in used:
                        used.add(symbol)
                        newNode = self.makeNewNode(cur, symbol)
                        new, changed = self.resolveDupes(newNode)
                        if symbol not in cur.trans:
                            cur.addTrans(symbol, new)
                        if changed and new not in todo:
                            todo.append(new)

        # normalize the node ID's
        for idx, n in enumerate(self.nodes):
            n.id = idx

    def makeClosure(self, node: Node) -> None:
        """
        Compute the LR(1) Closure of a node
        :param node: The node to compute
        :return: None
        """
        changed = True
        while changed:
            changed = False
            for annotRule in node.rules:
                if annotRule.indexAtEnd():
                    # The index is at the end, skip
                    continue

                nextSym = annotRule.nextSymbol()
                if nextSym.isTerminal:
                    # the next symbol is a terminal, skip
                    continue

                newLookAhead = annotRule.getNewLA()

                for rule in self.ruleLookup[nextSym]:
                    if node.addRule(rule, 0, newLookAhead.copy()):
                        changed = True
                # End for rule
            # End for annotRule
        # End while changed

    def makeNewNode(self, curNode: Node, symbol: Symbol) -> Node:
        newNode = Node(self.nodeIDs)
        self.nodeIDs += 1

        for annotR in curNode.rules:
            if not annotR.indexAtEnd() and annotR.nextSymbol() == symbol:
                newNode.addRule(annotR.rule, annotR.parseIndex + 1, annotR.lookAhead.copy())

        self.makeClosure(newNode)
        return newNode

    def resolveDupes(self, newNode: Node) -> Tuple[Node, bool]:
        for node in self.nodes:
            if node.canCombine(newNode):
                # Decrement the ID
                self.nodeIDs -= 1
                return node, node.combine(newNode)

        # If we got here it is a new node
        self.nodes.append(newNode)
        return newNode, True


def writeDescription(filename: str, lalr: LALR1Automata):
    with open(filename, mode='w') as f:
        for node in lalr.nodes:
            f.write(str(node))
            f.write("\n  Rules:\n")

            for rule in node.rules:
                f.write(f"    {rule.strRule()} {rule.lookAhead}\n")

            if len(node.trans) > 0:
                f.write('\n  Transitions:\n')

                for key, val in node.trans.items():
                    f.write(f"    on {key} -> {val}\n")

            f.write("\n")
