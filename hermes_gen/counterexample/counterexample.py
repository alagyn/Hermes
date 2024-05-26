from collections import deque
from typing import Deque, List, Dict, Set, Tuple
import time

from ..grammar import Grammar, Symbol
from ..lalr1_automata import LALR1Automata, Node, AnnotRule

from .stateItem import StateItem
from .configurations import Configuration, ComplexityQueue, ComplexityConfiguration


class CounterExampleGen:

    def __init__(self, automata: LALR1Automata) -> None:
        self.automata = automata
        StateItem.initLookups(automata)

    def generate_counterexample(
        self,
        conflictState: Node,
        conflictRule1: AnnotRule,
        conflictRule2: AnnotRule,
        conflictSymbol: Symbol,
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

        # Get the shortest path to the reduce rule
        shortestConflictPath = self._getShortestPathFromStart(conflictState, item1, conflictSymbol)
        # set of nodes used in the shortest path
        scpSet: Set[Node] = set()
        # set of states that use the conflicted nonterminal
        reduceProdSet: Set[Node] = set()

        reduceProdReached = False
        for state in shortestConflictPath:
            scpSet.add(state.node)
            reduceProdReached = reduceProdReached or state.rule.rule.nonterm == item1.rule.nonterm
            if reduceProdReached:
                reduceProdSet.add(state.node)

        # Actually compute counterexample
        startTime = time.perf_counter()

        # priority queue of search states
        pq = ComplexityQueue()
        complexityMap: Dict[int, ComplexityConfiguration] = {}
        visited = {}

        def addSearchState(state: Configuration):
            visited1 = visited[state.states1]
            if state.states2 in visited1:
                return
            try:
                cconfig = complexityMap[state.complexity]
            except KeyError:
                cconfig = ComplexityConfiguration(state.complexity)
                complexityMap[state.complexity] = cconfig
            cconfig.add(state)

    def _getShortestPathFromStart(
        self,
        tgtNode: Node,
        tgtRule: AnnotRule,
        conflictSym: Symbol,
        optimized: bool = True,
    ) -> Deque[StateItem]:

        source = StateItem.getStateItem(self.automata.start, self.automata.start.rules[0])
        target = StateItem.getStateItem(tgtNode, tgtRule)

        eligible = self._eligibleStateItemsToConflict(target) if optimized else None

        queue: Deque[Deque[StateItem]] = deque()
        queue.append(deque([source]))

        # add any other rules for the start symbol
        for rule in self.automata.start.rules[1:]:
            if rule.rule.nonterm == source.rule.rule.nonterm:
                queue.append(deque([StateItem.getStateItem(self.automata.start, rule)]))

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
                for symbold, nextSI in StateItem.FWD_TRANS[last].items():
                    if eligible is not None and nextSI not in eligible:
                        continue
                    nextPath = path.copy()
                    nextPath.append(nextSI)
                    queue.append(nextPath)
            except KeyError:
                pass
            # productions
            try:
                for nextSI in StateItem.FWD_PROD[last]:
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
                for prevSet in StateItem.REV_TRANS[state].values():
                    queue.extend(prevSet)
            except KeyError:
                pass
            if state.rule.parseIndex == 0:
                symbol = state.rule.rule.nonterm
                try:
                    revProd = StateItem.REV_PROD[state.node]
                    for prev in revProd[symbol]:
                        queue.append(prev)
                except KeyError:
                    pass

        return out
