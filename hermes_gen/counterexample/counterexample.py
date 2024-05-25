from ..grammar import Grammar
from ..lalr1_automata import LALR1Automata, Node, AnnotRule

from .stateItem import StateItem
from .transitionTable import TransitionTable

from collections import deque
from typing import Deque, List, Dict, Set, Tuple


class _Configuration:

    def __init__(self) -> None:
        self.items = deque()
        self.derivs = deque()


class CounterExampleGen:

    def __init__(self, automata: LALR1Automata) -> None:
        self.automata = automata
        self.trans = TransitionTable(automata)

    def generate_counterexample(
        self,
        conflictState: Node,
        conflictRule1: AnnotRule,
        conflictRule2: AnnotRule,
        conflictSymbol: str,
    ):
        """
        Counterexample algorithm as described in 
        'Finding Counterexamples from Parsing Conflicts' [Isradisaikul, Myers] (2015)
        """

        # If this is a S/R conflict, we want the R to be item 1
        # otherwise, it doesn't matter
        if conflictRule1.indexAtEnd():
            # our first rule is a reduce rule, check the second
            if conflictRule2.indexAtEnd():
                # we have a R/R conflict
                isShiftReduce = False
            else:
                # we have a S/R
                isShiftReduce = True

            # order doesn't matter if R/R, but we def want item1
            # to be a reduce item
            item1 = conflictRule1
            item2 = conflictRule2
        elif conflictRule2.indexAtEnd():
            # out second rule is a reduce, but the first is a shift
            isShiftReduce = True
            item1 = conflictRule2
            item2 = conflictRule1
        else:
            # shouldn't ever reach here?
            # S/S conflicts are impossible
            raise RuntimeError("generate_counterexample() Expected at least one reduce rule")

        path = self._getShortestPathFromStart(conflictState, item1, conflictSymbol)

        for x in path:
            print(x.rule.rule.nonterm, end=" ")
        print("")

    def _getShortestPathFromStart(
        self,
        tgtNode: Node,
        tgtRule: AnnotRule,
        conflictSym: str,
        optimized: bool = True,
    ) -> Deque[StateItem]:

        source = self.trans.getStateItem(self.automata.start, self.automata.start.rules[0])
        target = self.trans.getStateItem(tgtNode, tgtRule)

        eligible = self._eligibleStateItemsToConflict(target) if optimized else None

        queue: Deque[Deque[StateItem]] = deque()
        queue.append(deque([source]))

        # add any other rules for the start symbol
        for rule in self.automata.start.rules[1:]:
            if rule.rule.nonterm == source.rule.rule.nonterm:
                queue.append(deque([self.trans.getStateItem(self.automata.start, rule)]))

        visited: Set[StateItem] = set()

        # breadth-first search
        while len(queue) > 0:
            path = queue.popleft()
            last = path[-1]
            #print(last.node, last.rule)
            if last in visited:
                continue
            visited.add(last)
            if target == last and conflictSym in last.rule.lookAhead:
                # done
                return path
            # transitions
            try:
                for symbold, nextSI in self.trans.fwd[last].items():
                    if eligible is not None and nextSI not in eligible:
                        continue
                    nextPath = path.copy()
                    nextPath.append(nextSI)
                    queue.append(nextPath)
            except KeyError:
                pass
            # productions
            try:
                for nextSI in self.trans.prods[last]:
                    if eligible is not None and nextSI not in eligible:
                        continue
                    nextPath = path.copy()
                    nextPath.append(nextSI)
                    queue.append(nextPath)
            except KeyError:
                pass

        raise RuntimeError("Failed to find shortest path")

    def _eligibleStateItemsToConflict(self, target: StateItem) -> Set[StateItem]:
        out = set()

        queue: Deque[StateItem] = deque()
        queue.append(target)

        while len(queue) > 0:
            state = queue.popleft()
            if state in out:
                continue
            out.add(state)
            # consider reverse transitions and reverse productions
            try:
                for prevSet in self.trans.rev[state].values():
                    queue.extend(prevSet)
            except KeyError:
                pass
            if state.rule.parseIndex == 0:
                symbol = state.rule.rule.nonterm
                try:
                    revProd = self.trans.revProds[state.node]
                    for prev in revProd[symbol]:
                        queue.append(prev)
                except KeyError:
                    pass

        return out
