from typing import Dict, List, Tuple, Optional, Set
from collections import deque
import itertools

from hermes_gen.ebnf_grammer import Grammer, Rule
from hermes_gen.first_and_follow import FirstAndFollow
from hermes_gen.consts import END, EMPTY
from hermes_gen.errors import PTGError


class AnnotRule:
    """
    A rule combined with a parse index and a look ahead
    """

    def __init__(self, rule: Rule, parseIndex: int, lookAhead: set[str]) -> None:
        """
        :param rule: The Rule
        :param parseIndex: The index of the symbol AFTER the dot, i.e. the symbol we are looking for
        :param lookAhead: The look ahead set for the rule
        """
        self.rule = rule
        self.parseIndex = parseIndex
        self.lookAhead = lookAhead

    def __str__(self) -> str:
        out = f'AnnotRule: {self.rule.nonterm} ='

        for i in range(self.parseIndex):
            out += " " + self.rule.symbols[i]

        out += " ."

        for i in range(self.parseIndex, len(self.rule.symbols)):
            out += " " + self.rule.symbols[i]

        out += f"  LA: {self.lookAhead}"

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

    def nextSymbol(self) -> str:
        """
        Get the next symbol
        """
        return self.rule.symbols[self.parseIndex]

    def getNewLA(self, g: Grammer, ff: FirstAndFollow) -> set[str]:
        """
        Returns the lookahead for closure rules generated from this rule
        Uses set of symbols that can be collapsed after the next symbol to be
        consumed (i.e. every symbol from idx + 1 up to and including
        the first that can't be null)
        :param g: The grammer
        :param ff: The first and follow sets
        :return: The lookahead
        """

        out = set()
        for i in range(self.parseIndex + 1, len(self.rule.symbols)):
            symbol = self.rule.symbols[i]
            out.update(ff.first[symbol])
            if symbol not in g.nulls:
                return out

        # If we got here, every symbol after the next can be nulled
        # Add our own look ahead
        out.update(self.lookAhead)
        return out


class Node:

    def __init__(self, id: int) -> None:
        self.id = id
        self.rules: List[AnnotRule] = []
        # Map of transitions
        self.trans: Dict[str, Node] = {}

    def __str__(self) -> str:
        return f'Node#{self.id}'

    def addRule(self, rule: Rule, parseIndex: int, lookAhead: set[str]) -> bool:
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

    def addTrans(self, nt: str, node: 'Node'):
        if nt in self.trans:
            raise PTGError(
                f"LALR: Node: {str(self)}\n"
                f"Attempted to add duplicate transition on NT: {nt}\n"
                f"Existing: {str(self.trans[nt])}\n"
                f"New: {str(node)}"
            )

        self.trans[nt] = node


class LALR1Automata:

    def __init__(self, g: Grammer, ff: FirstAndFollow) -> None:
        # Start node is ID 0
        self.start = Node(0)
        # start IDs at 1
        self.nodeIDs = 1

        self.grammer = g
        self.ff = ff

        # Lookup rules for each nonterminal
        self.ruleLookup: Dict[str, List[Rule]] = {}
        for rule in g.rules:
            try:
                self.ruleLookup[rule.nonterm].append(rule)
            except KeyError:
                self.ruleLookup[rule.nonterm] = [rule]

        # Add all the rules for the start symbol to the start node
        for rule in self.ruleLookup[g.startSymbol]:
            self.start.addRule(rule, 0, {END})

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
                if nextSym in self.grammer.terminals:
                    # the next symbol is a terminal, skip
                    continue

                newLookAhead = annotRule.getNewLA(self.grammer, self.ff)

                for rule in self.ruleLookup[nextSym]:
                    if node.addRule(rule, 0, newLookAhead.copy()):
                        changed = True
                # End for rule
            # End for annotRule
        # End while changed

    def makeNewNode(self, curNode: Node, symbol: str) -> Node:
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


class Action:
    S = 'S'
    R = 'R'
    G = 'G'
    E = 'E'
    A = 'A'


class ParseAction:

    def __init__(self, action=Action.E, state=0, rule: Optional[AnnotRule] = None) -> None:
        self.action = action
        self.state = state
        self.rule = rule

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParseAction):
            return False

        return self.action == other.action and self.state == other.state

    def __str__(self) -> str:
        return f'{self.action}{self.state} {self.rule}'


RowType = List[ParseAction]
TableType = List[RowType]


class ParseTable:

    def _conflict(self, node: Node, symbol: str, first: ParseAction, second: ParseAction):
        raise PTGError(
            f'Parse Table: Cannot build parse table, conflict: {node}, Symbol: {symbol}\n'
            f'\tA1: {first}\n'
            f'\tA2: {second}'
        )

    def __init__(self, automata: LALR1Automata) -> None:

        self.symbolList = []
        for x in sorted(automata.ruleLookup.keys()):
            if x != automata.grammer.startSymbol:
                self.symbolList.append(x)

        self.symbolList.extend([x[0] for x in automata.grammer.terminalList])
        self.symbolList.append(END)

        self.symbolIDs: Dict[str, int] = {
            x: idx
            for idx, x in enumerate(self.symbolList)
        }

        self.table: TableType = []
        for node in automata.nodes:
            curRow: RowType = [ParseAction() for _ in self.symbolIDs]
            self.table.append(curRow)

            for rule in node.rules:
                if rule.indexAtEnd():
                    for terminal in rule.lookAhead:
                        if terminal == EMPTY:
                            continue
                        termID = self.symbolIDs[terminal]
                        curActionTuple = curRow[termID]
                        newActionTuple = ParseAction(Action.R, rule.rule.id, rule)
                        if curActionTuple != ParseAction() and curActionTuple != newActionTuple:
                            self._conflict(node, terminal, curActionTuple, newActionTuple)

                        curRow[termID] = newActionTuple
                    continue

                nextSymbol = rule.nextSymbol()
                nextSymbolID = self.symbolIDs[nextSymbol]
                nextNode = node.trans[nextSymbol].id

                if nextSymbol in automata.grammer.terminals:
                    nextAction = Action.S
                else:
                    nextAction = Action.G

                newActionTuple = ParseAction(nextAction, nextNode, rule)
                curActionTuple = curRow[nextSymbolID]
                if curActionTuple != ParseAction() and curActionTuple != newActionTuple:
                    self._conflict(node, nextSymbol, curActionTuple, newActionTuple)

                curRow[nextSymbolID] = newActionTuple
            # End for rule in node
        # End for node in automata

    def printTable(self):
        print("   ", end="")
        for x in self.symbolList:
            print(f'{x:10s}', end="")
        print("")

        for idx, row in enumerate(self.table):
            print(f'{idx}: ', end="")
            for x in row:
                if x.action == Action.E:
                    print("          ", end="")
                else:
                    print(f'{x.action}{x.state}        ', end="")
            print("")
        print("")