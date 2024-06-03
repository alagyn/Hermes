from typing import Optional, Dict, List

from .lalr1_automata import AnnotRule, Node, LALR1Automata
from .grammar import Symbol
from hermes_gen.consts import END, EMPTY
from .counterexample.counterexampleGen import CounterExampleGen, CounterExample, isConflictShiftReduce
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


class Conflict:

    def __init__(self, node: Node, symbol: Symbol, first: AnnotRule, second: AnnotRule) -> None:
        self.node = node
        self.symbol = symbol
        self.rule1 = first
        self.rule2 = second
        self.counter: Optional[CounterExample] = None


RowType = List[ParseAction]
TableType = List[RowType]


class ParseTable:

    def __init__(self, automata: LALR1Automata) -> None:
        self.automata = automata

        self._counterExampleGen: Optional[CounterExampleGen] = None
        self.conflicts: List[Conflict] = []

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
                            self._reportConflict(node, terminal, curActionTuple, newActionTuple)

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
                    self._reportConflict(node, nextSymbol, curActionTuple, newActionTuple)

                    # TODO conflict resolution
                    # right now we just always take the shift action
                    if newActionTuple.action == Action.S:
                        curRow[nextSymbolID] = newActionTuple
                else:
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

    def _reportConflict(self, node: Node, symbol: Symbol, first: ParseAction, second: ParseAction):
        if first.rule is None or second.rule is None:
            raise RuntimeError("Invalid parse actions")

        self.conflicts.append(Conflict(node, symbol, first.rule, second.rule))

    def printConflicts(self, genCounterexamples: bool):
        if genCounterexamples:
            self._counterExampleGen = CounterExampleGen(self.automata)
            for c in self.conflicts:
                ce = self._counterExampleGen.generate_counterexample(c.node, c.rule1, c.rule2, c.symbol)
                self._printCounterexample(c, ce)
        else:
            for c in self.conflicts:
                message = [f"Warning: conflict detected in {c.node}"]
                isShiftReduce, item1, item2 = isConflictShiftReduce(c.rule1, c.rule2)
                message.append(f"  Conflict Type: {'Shift-Reduce' if isShiftReduce else 'Reduce-Reduce'}")
                message.append(f"  Symbol: {c.symbol}")
                if isShiftReduce:
                    message.append(f'  Reduce: {item1}')
                    message.append(f'   Shift: {item2}')
                else:
                    message.append(f'  Reduce 1: {item1}')
                    message.append(f'  Reduce 2: {item2}')
                message.append("")
                print("\n".join(message))

    def _printCounterexample(self, c: Conflict, ce: CounterExample):
        message = [
            f'Warning: conflict detected in {c.node}',
        ]

        try:

            message.append(f"  Conflict Type: {'Shift-Reduce' if ce.isShiftReduce else 'Reduce-Reduce'}")

            if ce.isShiftReduce:
                if c.rule1.indexAtEnd():
                    message.append(f"  Reduce: {c.rule1.rule}")
                    message.append(f'   Shift: {c.rule2.rule}')
                else:
                    message.append(f"  Reduce: {c.rule2.rule}")
                    message.append(f'   Shift: {c.rule1.rule}')
            else:
                message.append(f'  Reduce 1: {c.rule1.rule}')
                message.append(f'  Reduce 2: {c.rule2.rule}')

            message.append("")

            if ce.unifying:
                message.append("  Unifying example found")
                message.append(f"  Ambiguity for nonterminal: {ce.nonTerminal()}")
                message.append("  Example:")
                message.append(f'    {ce.prettyExample1()}')

                message.append("")

                if ce.isShiftReduce:
                    message.append("  Derivation using reduction:")
                else:
                    message.append("  Derivation using reduction 1:")
                message.append(f'    {ce.example1()}')

                if ce.isShiftReduce:
                    message.append("  Derivation using shift:")
                else:
                    message.append("  Derivation using reduction 2:")

                message.append(f'    {ce.example2()}')
            else:
                message.append("  No Unifying example found")

                if ce.isShiftReduce:
                    message.append("  Example using reduction:")
                else:
                    message.append("  Example using reduction 1:")
                message.append(f'    {ce.prettyExample1()}')
                message.append("  Derivation:")
                message.append(f'    {ce.example1()}')

                message.append("")

                if ce.isShiftReduce:
                    message.append("  Example using shift:")
                else:
                    message.append("  Example using reduction 2:")
                message.append(f'    {ce.prettyExample2()}')
                message.append("  Derivation:")
                message.append(f'    {ce.example2()}')
            print("\n".join(message))
            print("")
        except Exception as err:
            print("\n".join(message))
            print("  Unable to generate counterexample:", err)
