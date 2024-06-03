from collections import deque, defaultdict
from typing import Deque, List, Dict, Set, Tuple, Optional
import time

from ..grammar import Grammar, Symbol
from ..lalr1_automata import LALR1Automata, Node, AnnotRule
from ..errors import HermesError

from .stateItem import StateItem, productionAllowed
from .configurations import Configuration, ComplexityQueue, ComplexityConfiguration, nullableClosure
from .counterexample import CounterExample
from .conflict import Conflict
from .derivation import Derivation, DOT
from .utils import sliceDeque
from . import costs

ASSURANCE_LIMIT_SEC = 2
TIME_LIMIT_SEC = 5


class CounterExampleGen:

    def __init__(self, automata: LALR1Automata) -> None:
        self.automata = automata
        StateItem.initLookups(automata)

        self.timeLimitEnforced = True

        self._conflictSymbol: Symbol = None  # type: ignore

    def generate_counterexample(self, conflict: Conflict) -> CounterExample:
        """
        Counterexample algorithm as described in 
        'Finding Counterexamples from Parsing Conflicts' [Isradisaikul, Myers] (2015)
        """

        self._conflictSymbol = conflict.symbol

        isShiftReduce = conflict.isShiftReduce
        item1 = conflict.rule1
        item2 = conflict.rule2

        # Get the shortest path to the reduce rule
        shortestConflictPath = self._getShortestPathFromStart(conflict.node, item1)
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
                pq.push(cconfig)
            cconfig.add(cfg)

        def addVisited(cfg: Configuration):
            visited1 = visited[tuple(cfg.states1)]
            visited1.add(tuple(cfg.states2))

        initial = Configuration()
        stateItem1 = StateItem.getStateItem(conflict.node, item1)
        stateItem2 = StateItem.getStateItem(conflict.node, item2)
        initial.states1.append(stateItem1)
        initial.states2.append(stateItem2)

        addSearchState(initial)
        stage3Result: Optional[Configuration] = None
        assurancePrinted = False
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
                            return CounterExample(conflict, cfg.derivs1[0], cfg.derivs2[0], unifying=True)
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
                    dur = time.perf_counter() - startTime
                    if not assurancePrinted and dur > ASSURANCE_LIMIT_SEC:
                        print("Looking for conflict counterexamples...")
                        assurancePrinted = True
                    if dur > TIME_LIMIT_SEC:
                        print("Time limit exceeded")
                        if stage3Result is not None:
                            return self._completeDivergingExamples(conflict, stage3Result, timeout=True)
                        else:
                            return self._exampleFromShortestPath(conflict, shortestConflictPath, True)
                # end if timelimit

                # Compute the successor configurations.
                si1 = cfg.states1[-1]
                si2 = cfg.states2[-1]
                si1reduce = si1.rule.indexAtEnd()
                si2reduce = si2.rule.indexAtEnd()
                si1sym = si1.transSymbol
                si2sym = si2.transSymbol
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
                        if si1.transItem is None or si2.transItem is None:
                            raise RuntimeError()

                        si1last = si1.transItem
                        si2last = si2.transItem

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

                        for i in range(1, len(derivs1) + 1):
                            subderivs1 = sliceDeque(derivs1, 0, i)
                            substates1 = sliceDeque(states1, 0, i)
                            for j in range(1, len(derivs2) + 1):
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
                        if symbol1.isTerminal:
                            return
                        for item in si.fwdProd:
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
                            for i in range(len(derivs) + 1):
                                subderivs = sliceDeque(derivs, 0, i)
                                substates = sliceDeque(states, 0, i + 1)
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
                                if side == 2 and cfg.shiftDepth >= 0:
                                    copy.shiftDepth += 1
                                copy.complexity += costs.PRODUCTION_COST
                                addSearchState(copy)
                        # end for production

                    # end takeProdStep

                    # take a production step if possible
                    takeProdStep(si1sym, si2sym, si1, 1)
                    takeProdStep(si2sym, si1sym, si2, 2)

                # end if both shift
                else:
                    # one of the paths requires a reduction
                    ready1 = si1reduce and len(cfg.states1) > len(si1.rule)
                    ready2 = si2reduce and len(cfg.states2) > len(si2.rule)
                    # If there is a path ready for reduction
                    # without being prepended further, reduce.
                    if ready1:
                        reduced1 = cfg.reduce1(si2sym, stateItem1)
                        if ready2:
                            reduced1.append(cfg)
                            for red1 in reduced1:
                                for candidate in red1.reduce2(si1sym, stateItem2):
                                    addSearchState(candidate)
                                # avoid duplicates
                                if si1reduce and red1 != cfg:
                                    addSearchState(red1)
                        else:
                            for candidate in reduced1:
                                addSearchState(candidate)
                    elif ready2:
                        reduced2 = cfg.reduce2(si1sym, stateItem2)
                        for candidate in reduced2:
                            addSearchState(candidate)
                    else:
                        # Otherwise, prepend both paths and continue.
                        # This is preparing both paths for a reduction.
                        sym = None
                        if si1reduce and not ready1:
                            sym = si1.rule[len(si1.rule) - len(cfg.states1)]
                        else:
                            sym = si2.rule[len(si2.rule) - len(cfg.states2)]
                        # TODO extended search?
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
        return self._exampleFromShortestPath(conflict, shortestConflictPath, False)

    def _exampleFromShortestPath(
        self, c: Conflict, shortestConflictPath1: Deque[StateItem], timeout: bool
    ) -> CounterExample:
        if not c.isShiftReduce:
            # For reduce/reduce conflicts, simply find the shortest
            # lookahead-sensitive path to the other conflict item.
            shortestConflictPath2 = self._getShortestPathFromStart(c.node, c.rule2)
            deriv1 = self._completeDivergingExample(shortestConflictPath1, deque())
            deriv2 = self._completeDivergingExample(shortestConflictPath2, deque())
            return CounterExample(c, deriv1, deriv2, False, timeout=timeout)
        si = StateItem.getStateItem(c.node, c.rule2)
        out: Deque[StateItem] = deque()
        out.append(si)

        itr = iter(reversed(shortestConflictPath1))
        refsi = next(itr, None)
        while refsi is not None:
            # Construct a list of items in the same state as refsi.
            # prevrefsi is the last StateItem in the previous state.
            refsis: Deque[StateItem] = deque()
            refsis.append(refsi)
            prevrefsi = next(itr, None)
            if prevrefsi is not None:
                curPos = refsi.rule.parseIndex
                prevPos = prevrefsi.rule.parseIndex
                while prevrefsi is not None and prevPos + 1 != curPos:
                    refsis.appendleft(prevrefsi)
                    curPos = prevPos
                    prevrefsi = next(itr, None)
                    if prevrefsi is not None:
                        prevPos = prevrefsi.rule.parseIndex
            if si == refsi or si.rule == StateItem.AUTOMATA.start.rules[0]:
                # reached the common item, prepend to the beginning
                refsis.pop()
                # reversed since this will reverse the list
                out.extendleft(reversed(refsis))
                if prevrefsi is not None:
                    out.appendleft(prevrefsi)
                # add everything else
                try:
                    while True:
                        out.appendleft(next(itr))
                except StopIteration:
                    pass
                deriv1 = self._completeDivergingExample(shortestConflictPath1, deque())
                deriv2 = self._completeDivergingExample(out, deque())
                return CounterExample(c, deriv1, deriv2, False, timeout=timeout)

            pos = si.rule.parseIndex
            if pos == 0:
                # For a production item, find a sequence of items within the
                # same state that leads to this production.
                queue: Deque[Deque[StateItem]] = deque()
                queue.append(deque([si]))
                while len(queue) > 0:
                    sis = queue.popleft()
                    sisrc = sis[0]
                    if sisrc.rule == StateItem.AUTOMATA.start.rules[0]:
                        sis.pop()
                        out.extendleft(reversed(sis))
                        si = sisrc
                        break
                    srcpos = sisrc.rule.parseIndex
                    if srcpos > 0:
                        sym = sisrc.rule[srcpos - 1]
                        for prevsi in sisrc.revTrans[sym]:
                            if prevrefsi is not None and prevsi.node != prevrefsi.node:
                                continue
                            sis.pop()
                            out.extendleft(reversed(sis))
                            out.appendleft(prevsi)
                            si = prevsi
                            refsi = prevrefsi
                            queue.clear()
                            break
                    else:
                        # take a reverse production step if possible
                        for prevsi in sisrc.revProd[sisrc.rule.rule.nonterm]:
                            if prevsi in sis:
                                continue
                            prevsis = sis.copy()
                            prevsis.appendleft(prevsi)
                            queue.append(prevsis)
                    # end else
                # end while queue
            # end if pos == 0
            else:
                # if not a production item, make a reverse transition
                for prevsi in si.revTrans[si.rule[pos - 1]]:
                    # Only look for state compatible with the shortest path.
                    if prevrefsi is not None and prevsi.node != prevrefsi.node:
                        continue
                    out.appendleft(prevsi)
                    si = prevsi
                    refsi = prevrefsi
                    break
            # end else
        # end while itr

        raise HermesError("Cannot find derivation to conflict node")

    def _completeDivergingExamples(self, c: Conflict, cfg: Configuration, timeout: bool) -> CounterExample:
        derivs1 = self._completeDivergingExample(cfg.states1, cfg.derivs1)
        derivs2 = self._completeDivergingExample(cfg.states2, cfg.derivs2)
        return CounterExample(c, derivs1, derivs2, False, timeout=timeout)

    def _completeDivergingExample(self, states: Deque[StateItem], derivs: Deque[Derivation]) -> Derivation:
        out: Deque[Derivation] = deque()
        dItr = iter(reversed(derivs))
        sItr = iter(reversed(states))
        lookaheadRequired = False
        while True:
            si = next(sItr, None)
            if si is None:
                break
            pos = si.rule.parseIndex
            rLen = len(si.rule)
            # symbols after dot
            if len(out) == 0:
                if len(derivs) == 0:
                    out.append(DOT)
                    lookaheadRequired = True
                if not si.rule.indexAtEnd():
                    out.append(Derivation(si.rule.nextSymbol()))
                    lookaheadRequired = False
            i = pos + 1
            while i < rLen:
                sym = si.rule[i]
                if lookaheadRequired:
                    if sym != self._conflictSymbol:
                        if not sym.nullable or self._conflictSymbol in sym.first:
                            if si.transItem is None:
                                raise RuntimeError()
                            nextDerivs = self._expandFirst(si.transItem)
                            out.extend(nextDerivs)
                            i += len(nextDerivs) - 1
                            lookaheadRequired = False
                        else:
                            # This nonterminal is nullable and cannot derive the conflict symbol.
                            # So, this nonterminal must derive the empty string,
                            # and conflict must be derived by a later nonterminal.
                            out.append(Derivation(sym, []))
                    else:
                        out.append(Derivation(sym))
                        lookaheadRequired = False
                else:
                    out.append(Derivation(sym))
                i += 1
            # end while
            # symbols before dot
            i = pos - 1
            while i >= 0:
                next(sItr, None)
                d = next(dItr, None)
                if d is not None:
                    out.appendleft(d)
                else:
                    out.appendleft(Derivation(si.rule[i]))
                i -= 1
            # completing the derivation
            deriv = Derivation(si.rule.rule.nonterm, list(out))
            out = deque()
            out.append(deriv)
        # end while true
        return out[0]

    def _expandFirst(self, start: StateItem) -> Deque[Derivation]:
        """
        Repeatedly take production steps on the given StateItem so that the
        first symbol of the derivation matches the conflict symbol.
        """
        queue: Deque[Deque[StateItem]] = deque()
        queue.append(deque([start]))
        # breadth first search
        while len(queue) > 0:
            states = queue.popleft()
            silast = states[-1]
            sym = silast.rule.nextSymbol()
            if sym == self._conflictSymbol:
                # done: construct derivation
                out: Deque[Derivation] = deque()
                out.append(Derivation(sym))
                sItr = iter(reversed(states))
                while True:
                    si = next(sItr, None)
                    if si is None:
                        break
                    pos = si.rule.parseIndex
                    if pos == 0:
                        for i in range(pos + 1, len(si.rule)):
                            out.append(Derivation(si.rule[i]))
                        deriv = Derivation(si.rule.rule.nonterm, list(out))
                        out = deque()
                        out.append(deriv)
                    else:
                        deriv = Derivation(si.rule[pos - 1], [])
                        out.appendleft(deriv)
                # end while iter
                out.popleft()
                return out
            # end if sym is conflict
            if not sym.isTerminal:
                for item in silast.fwdProd:
                    if item in states:
                        continue
                    new = states.copy()
                    new.append(item)
                    queue.append(new)
                if sym.nullable:
                    # If the nonterminal after dot is nullable,
                    # we need to look further.
                    if silast.transItem is None or silast.transSymbol != sym:
                        raise RuntimeError()
                    nextsi = silast.transItem
                    new = states.copy()
                    new.append(nextsi)
                    queue.append(new)
            # end if not terminal
        # end while queue
        raise HermesError(
            f"CounterExampleGen._expandFirst() Should not reach here (expected symbol: {self._conflictSymbol}, item to be expanded: {repr(start)})"
        )

    def _getShortestPathFromStart(
        self,
        tgtNode: Node,
        tgtRule: AnnotRule,
        optimized: bool = True,
    ) -> Deque[StateItem]:

        # we enforce that there is only one production for the start symbol, so we only need
        # to add this one state
        source = StateItem.getStateItem(self.automata.start, self.automata.start.rules[0])
        target = StateItem.getStateItem(tgtNode, tgtRule)

        class StateItemWithLookahead:

            def __init__(self, si: StateItem, la: Set[Symbol]) -> None:
                self.si = si
                self.la = la

            def hash(self) -> int:
                return hash(self.si) * 31 + hash(tuple(self.la))

        eligible = self._eligibleStateItemsToConflict(target) if optimized else None

        queue: Deque[Deque[StateItemWithLookahead]] = deque()
        queue.append(deque([StateItemWithLookahead(source, source.rule.lookAhead)]))

        visited: Set[int] = set()

        # breadth-first search
        while len(queue) > 0:
            path = queue.popleft()
            last = path[-1]
            #print(last.node, last.rule)
            h = last.hash()
            if h in visited:
                continue
            visited.add(h)
            if target == last.si and self._conflictSymbol in last.la:
                # done
                return deque([x.si for x in path])
            # transitions
            nextSI = last.si.transItem
            if nextSI is not None:
                if eligible is None or nextSI in eligible:
                    nextPath = path.copy()
                    nextPath.append(StateItemWithLookahead(nextSI, last.la))
                    queue.append(nextPath)
            # productions
            if len(last.si.fwdProd) > 0:
                ruleLen = len(last.si.rule)
                pos = last.si.rule.parseIndex + 1
                # Compute possible terminals that can follow this production.
                lookahead: Set[Symbol] = set()
                while True:
                    if pos == ruleLen:
                        lookahead.update(last.la)
                        break
                    else:
                        sym = last.si.rule[pos]
                        if sym.isTerminal:
                            lookahead.add(sym)
                            break
                        else:
                            lookahead.update(sym.first)
                            if not sym.nullable:
                                break
                    pos += 1
                    if pos > ruleLen:
                        break
                # Try all possible production steps within this parser state.
                for nextSI in last.si.fwdProd:
                    if eligible is not None and nextSI not in eligible:
                        continue
                    new = StateItemWithLookahead(nextSI, lookahead)
                    newPath = path.copy()
                    newPath.append(new)
                    queue.append(newPath)

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
                for prevSet in state.revTrans.values():
                    queue.extend(prevSet)
            except KeyError:
                pass
            if state.rule.parseIndex == 0:
                symbol = state.rule.rule.nonterm
                try:
                    revProd = state.revProd
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
