from collections import deque, defaultdict
from typing import Deque, List, Dict, Set, Tuple, Optional
import time

from ..grammar import Grammar, Symbol
from ..lalr1_automata import LALR1Automata, Node, AnnotRule

from .stateItem import StateItem, productionAllowed
from .configurations import Configuration, ComplexityQueue, ComplexityConfiguration, nullableClosure
from .counterexample import CounterExample
from .derivation import Derivation
from .utils import sliceDeque
from . import costs

TIME_LIMIT_SEC = 5


class CounterExampleGen:

    def __init__(self, automata: LALR1Automata) -> None:
        self.automata = automata
        StateItem.initLookups(automata)

        self.timeLimitEnforced = True

    def generate_counterexample(
        self,
        conflictState: Node,
        conflictRule1: AnnotRule,
        conflictRule2: AnnotRule,
        conflictSymbol: Symbol,
    ) -> CounterExample:
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
        visited: Dict[Tuple[StateItem, ...], Set[Tuple[StateItem, ...]]] = defaultdict(set)

        def addSearchState(cfg: Configuration):
            visited1 = visited[tuple(cfg.states1)]
            if tuple(cfg.states2) in visited1:
                return
            try:
                cconfig = complexityMap[cfg.complexity]
            except KeyError:
                cconfig = ComplexityConfiguration(cfg.complexity)
                complexityMap[cfg.complexity] = cconfig
            cconfig.add(cfg)

        def addVisited(cfg: Configuration):
            visited1 = visited[tuple(cfg.states1)]
            visited1.add(tuple(cfg.states2))

        initial = Configuration()
        initial.states1.append(StateItem.getStateItem(conflictState, conflictRule1))
        initial.states2.append(StateItem.getStateItem(conflictState, conflictRule2))

        addSearchState(initial)
        stage3Result: Optional[Configuration] = None
        while len(pq) > 0:
            css = pq.pop()
            for cfg in css.configs:
                si1src = cfg.states1[0]
                si2src = cfg.states2[0]
                addVisited(cfg)
                if cfg.reduceDepth < 0 and cfg.shiftDepth < 0:
                    # We have completed the reduce and shift conflict items.
                    # Stage 3
                    if si1src.rule.rule.nonterm == si2src.rule.rule.nonterm and self._hasCommonPrefix(si1src.rule,
                                                                                                      si2src.rule):
                        # We have found that both paths begin with the same prefix.
                        if len(cfg.derivs1) == 1 and len(cfg.derivs2) == 1 and cfg.derivs1[0] == cfg.derivs2[0]:
                            # Each path has only one symbol to be processes, and
                            # they are the same.  This means that the derivation
                            # of this symbol is the unifying counterexample we are
                            # looking for.
                            return CounterExample(cfg.derivs1[0], cfg.derivs2[0], True)
                        # Otherwise, we have found a symbol that can begin the
                        # same sequence of symbols up to the conflict point.
                        # If unifying counterexample is not found, we will use
                        # this to construct a nonunifying counterexample that
                        # is as compact as possible, as this counterexample does
                        # not begin all the way from the start state.
                        if stage3Result is None:
                            stage3Result = cfg
                # end reduce/shift depth check

                if self.timeLimitEnforced:
                    # TODO log thinking...
                    if time.perf_counter() - startTime > TIME_LIMIT_SEC:
                        # TODO log timelimit exceeded
                        if stage3Result is not None:
                            return self._completeDivergingExamples(stage3Result, True)
                        else:
                            return self._exampleFromShortestPath(
                                isShiftReduce, conflictState, conflictSymbol, item1, item2, shortestConflictPath, True
                            )
                # end if timelimit

                # Compute the successor configurations.
                si1 = cfg.states1[-1]
                si2 = cfg.states2[-1]
                si1reduce = si1.rule.indexAtEnd()
                si2reduce = si2.rule.indexAtEnd()
                si1sym = None if si1reduce else si1.rule.nextSymbol()
                si2sym = None if si2reduce else si2.rule.nextSymbol()
                if not si1reduce and not si2reduce:
                    # Both paths are not reduce items, so it is possible to
                    # search forward in the parser state diagram.
                    # Two actions are possible:
                    # - Make a transition on the next symbol of the items,
                    #   if they are the same.
                    # - Take a production step, avoiding duplicates as necessary.
                    if si1sym is None or si2sym is None:
                        raise RuntimeError()

                    if si1sym == si2sym:
                        # Transition on the same next symbol, taking nullable
                        # symbol into account.
                        si1last = StateItem.FWD_TRANS[si1][si1sym]
                        si2last = StateItem.FWD_TRANS[si2][si2sym]

                        states1: Deque[StateItem] = deque()
                        states1.append(si1last)
                        derivs1: Deque[Derivation] = deque()
                        derivs1.append(Derivation(si1sym))

                        nullableClosure(si1.rule, si1.rule.parseIndex + 1, si1last, states1, derivs1)

                        states2: Deque[StateItem] = deque()
                        states2.append(si2last)
                        derivs2: Deque[Derivation] = deque()
                        derivs2.append(Derivation(si2sym))

                        nullableClosure(si2.rule, si2.rule.parseIndex + 1, si2last, states2, derivs2)

                        for i in range(1, len(derivs1)):
                            subderivs1 = sliceDeque(derivs1, 0, i)
                            substates1 = sliceDeque(states1, 0, i)
                            for j in range(1, len(derivs2)):
                                subderivs2 = sliceDeque(derivs2, 0, j)
                                substates2 = sliceDeque(states2, 0, j)

                                copy = cfg.copy()
                                copy.derivs1.extend(subderivs1)
                                copy.states1.extend(substates1)
                                copy.derivs2.extend(subderivs2)
                                copy.states2.extend(substates2)
                                copy.complexity += 2 * costs.SHIFT_COST
                                addSearchState(copy)
                        # end for subderiv
                    # end if same symbol

                    def takeProdStep(symbol1: Symbol, symbol2: Symbol, si: StateItem, side: int):
                        if symbol1.isTerminal or si not in StateItem.FWD_PROD:
                            return
                        for item in StateItem.FWD_PROD[si]:
                            # Take production step only if lhs is not nullable and
                            # if first rhs symbol is compatible with the other path
                            applicable = not item.rule.indexAtEnd() and self._compatible(
                                item.rule.nextSymbol(), symbol2
                            )
                            if not applicable or not productionAllowed(si1, item):
                                continue
                            derivs: Deque[Derivation] = deque()
                            states: Deque[StateItem] = deque()
                            states.append(item)
                            nullableClosure(item.rule, 0, item, states, derivs)
                            for i in range(len(derivs)):
                                subderivs = sliceDeque(derivs, 0, i)
                                substates = sliceDeque(states, 0, i)
                                copy = cfg.copy()
                                if side == 1:
                                    d = copy.derivs1
                                    s = copy.states1
                                else:
                                    d = copy.derivs2
                                    s = copy.states2
                                d.extend(subderivs)
                                s.extend(substates)

                                if item in s:
                                    copy.complexity += costs.DUPLICATE_PRODUCTION_COST
                                copy.complexity += costs.PRODUCTION_COST
                                addSearchState(copy)
                        # end for production

                    # end takeProdStep

                    # take a production step if possible
                    takeProdStep(si1sym, si2sym, si1, 1)
                    takeProdStep(si2sym, si1sym, si2, 2)

                    # end if production 1
                # end if both shift
                else:
                    # one of the paths requires a reduction
                    ready1 = si1reduce and len(cfg.states1) > len(si1.rule.rule.symbols)
                    ready2 = si2reduce and len(cfg.states2) > len(si2.rule.rule.symbols)
                    # If there is a path ready for reduction
                    # without being prepended further, reduce.
                    if ready1:
                        # TODO depth
                        reduced1 = cfg.reduce1(si2sym, 0)
                        if ready2:
                            reduced1.append(cfg)
                            for red1 in reduced1:
                                for candidate in red1.reduce2(si1sym):
                                    addSearchState(candidate)
                                # avoid duplicates
                                if si1reduce and red1 != cfg:
                                    addSearchState(red1)
                        else:
                            for candidate in reduced1:
                                addSearchState(candidate)
                    elif ready2:
                        reduced2 = cfg.reduce2(si1sym)
                        for candidate in reduced2:
                            addSearchState(candidate)
                    else:
                        # Otherwise, prepend both paths and continue.
                        # This is preparing both paths for a reduction.
                        sym = None
                        if si1reduce and not ready1:
                            sym = si1.rule.rule.symbols[len(si1.rule.rule.symbols) - len(cfg.states1)]
                        else:
                            sym = si2.rule.rule.symbols[len(si2.rule.rule.symbols) - len(cfg.states2)]
                        # TODO extended search
                        for prepended in cfg.prepend(sym,
                                                     None,
                                                     None,
                                                     reduceProdSet if cfg.reduceDepth >= 0 else scpSet,
                                                     False):
                            addSearchState(prepended)
                # end reduce
            # end for search state
            complexityMap.pop(css.complexity)
        # end while queue not empty

        # No unifying counterexamples.  Construct a counterexample from the
        # shortest lookahead-sensitive path.
        return self._exampleFromShortestPath(
            isShiftReduce, conflictState, conflictSymbol, item1, item2, shortestConflictPath, False
        )

    def _exampleFromShortestPath(
        self,
        isShiftReduce: bool,
        conflictNode: Node,
        conflictSym: Symbol,
        item1: AnnotRule,
        item2: AnnotRule,
        shortestConflictPath1: Deque[StateItem],
        timeout: bool
    ) -> CounterExample:
        if not isShiftReduce:
            # For reduce/reduce conflicts, simply find the shortest
            # lookahead-sensitive path to the other conflict item.
            shortestConflictPath2 = self._getShortestPathFromStart(conflictNode, item2, conflictSym)
            deriv1 = self._completeDivergingExample(shortestConflictPath1, deque())
            deriv2 = self._completeDivergingExample(shortestConflictPath2, deque())
            return CounterExample(deriv1, deriv2, False, timeout)
        si = StateItem.getStateItem(conflictNode, item2)
        out: Deque[StateItem] = deque()
        out.append(si)
        # TODO

    def _completeDivergingExamples(self, cfg: Configuration, timeout: bool) -> CounterExample:
        derivs1 = self._completeDivergingExample(cfg.states1, cfg.derivs1)
        derivs2 = self._completeDivergingExample(cfg.states2, cfg.derivs2)
        return CounterExample(derivs1, derivs2, False, timeout)

    def _completeDivergingExample(self, states: Deque[StateItem], derivs: Deque[Derivation]) -> Derivation:
        # TODO
        pass

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

    def _hasCommonPrefix(self, rule1: AnnotRule, rule2: AnnotRule) -> bool:
        if rule1.parseIndex != rule2.parseIndex:
            return False
        for i in range(rule1.parseIndex):
            if rule1.rule.symbols[i] != rule2.rule.symbols[i]:
                return False
        return True

    def _compatible(self, sym1: Symbol, sym2: Symbol) -> bool:
        """
        Determine if the given symbols are compatible with each other.
        That is, if both are terminals, they must be the same; otherwise, if
        one is a terminal and the other a nonterminal, the terminal must be a
        possible beginning of the nonterminal; finally, if both are nonterminals,
        their first sets must intersect.
        """

        if sym1.isTerminal:
            if sym2.isTerminal:
                return sym1 == sym2
            return sym1 in sym2.first
        elif sym2.isTerminal:
            return sym2 in sym1.first
        else:
            return sym1 == sym2 or len(sym1.first & sym2.first) > 0
