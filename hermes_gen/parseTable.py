from typing import Optional, Dict, List

from .lalr1_automata import AnnotRule, Node, LALR1Automata
from .grammar import Symbol
from hermes_gen.consts import END, EMPTY
from .counterexample.counterexample import CounterExampleGen
from .errors import HermesError


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

    def __repr__(self) -> str:
        return str(self)


RowType = List[ParseAction]
TableType = List[RowType]


class ParseTable:

    def _conflict(self, node: Node, symbol: Symbol, first: ParseAction, second: ParseAction):
        if self._counterExampleGen is None:
            self._counterExampleGen = CounterExampleGen(self.automata)

        if first.rule is None or second.rule is None:
            raise RuntimeError("Invalid parse actions")

        self._counterExampleGen.generate_counterexample(node, first.rule, second.rule, symbol)
        raise HermesError(
            f'Parse Table: Cannot build parse table, conflict: {node}, Symbol: {symbol}\n'
            f'\tA1: {first}\n'
            f'\tA2: {second}'
        )

    def __init__(self, automata: LALR1Automata) -> None:
        self.automata = automata

        self._counterExampleGen: Optional[CounterExampleGen] = None

        # Every symbol in the order they appear in the parse table
        self.symbolList = [automata.grammar.startSymbol]

        self.terminals: List[Symbol] = []
        self.nonterminals: List[Symbol] = []

        for x in Symbol.all():
            if x not in {automata.grammar.startSymbol, Symbol.EMPTY_SYMBOL, Symbol.END_SYMBOL}:
                if x.isTerminal:
                    self.terminals.append(x)
                else:
                    self.nonterminals.append(x)

        # Sort by ID so that they are put in the order they were defined
        # since this defines precedence
        self.terminals.sort(key=lambda x: x.id)
        # Sort nonterminals alphabetically
        self.nonterminals.sort()

        self.symbolList.extend(self.nonterminals)
        self.symbolList.extend(self.terminals)
        self.symbolList.append(Symbol.END_SYMBOL)

        self.symbolIDs: Dict[Symbol, int] = {
            x: idx - 1
            for idx, x in enumerate(self.symbolList)
        }

        self.table: TableType = []
        for node in automata.nodes:
            # -1 to remove start symbol
            curRow: RowType = [ParseAction() for _ in range(len(self.symbolList) - 1)]
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

                if nextSymbol.isTerminal:
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
