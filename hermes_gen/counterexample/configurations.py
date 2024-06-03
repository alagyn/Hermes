from collections import deque
from typing import Deque, Set, Optional, List
import heapq

from ..lalr1_automata import Node, AnnotRule
from ..grammar import Symbol
from ..errors import HermesError
from .stateItem import StateItem, intersect, intersectSet
from .derivation import Derivation, DOT
from . import costs
from .utils import sliceDeque


def countProductionSteps(items: Deque[StateItem], last: StateItem):
    count = 0
    lastState = last.node
    for x in reversed(items):
        if x.node == lastState:
            count += 1
        lastState = x.node
    return count


def nullableClosure(
    rule: AnnotRule, pos: int, siLast: StateItem, states: Deque[StateItem], derivs: Deque[Derivation]
) -> None:
    for i in range(pos, len(rule)):
        symbol = rule[i]
        if symbol.isTerminal or not symbol.nullable:
            break
        if siLast.transItem is None:
            break
        siLast = siLast.transItem
        derivs.append(Derivation(symbol, []))
        states.append(siLast)


class Configuration:

    def __init__(self) -> None:
        self.states1: Deque[StateItem] = deque()
        self.states2: Deque[StateItem] = deque()
        self.derivs1: Deque[Derivation] = deque()
        self.derivs2: Deque[Derivation] = deque()
        self.complexity = 0
        # The number of production steps made since the reduce conflict item.
        #   If this is -1, the reduce conflict item has been completed.
        self.reduceDepth = 0
        # The number of production steps made since the shift conflict item.
        #  If this is -1, the shift conflict item has been completed and
        #  reduced.
        self.shiftDepth = 0

    def copy(self) -> 'Configuration':
        out = Configuration()
        out.states1 = self.states1.copy()
        out.states2 = self.states2.copy()
        out.derivs1 = self.derivs1.copy()
        out.derivs2 = self.derivs2.copy()
        out.complexity = self.complexity
        out.reduceDepth = self.reduceDepth
        out.shiftDepth = self.shiftDepth
        return out

    def prepend(
        self,
        sym: Symbol,
        nextSym1: Optional[Symbol],
        nextSym2: Optional[Symbol],
        guide: Optional[Set[Node]],
        extendedSearch: bool
    ) -> List['Configuration']:
        out: List[Configuration] = []

        si1src = self.states1[0]
        si2src = self.states2[0]

        if nextSym1 is None:
            si1lookahead = si1src.rule.lookAhead
        else:
            si1lookahead = {nextSym1}

        if nextSym2 is None:
            si2lookahead = si2src.rule.lookAhead
        else:
            si2lookahead = {nextSym2}

        prev1: Optional[Set[Optional[StateItem]]] = None
        prev2: Optional[Set[Optional[StateItem]]] = None
        if extendedSearch:
            prev1 = set(si1src.reverseTransition(sym, si1lookahead, guide))
            prev2 = set(si2src.reverseTransition(sym, si2lookahead, guide))

        prev1ext: List[Optional[StateItem]
                       ] = si1src.reverseTransition(sym, si1lookahead, None if extendedSearch else guide)
        prev2ext: List[Optional[StateItem]
                       ] = si2src.reverseTransition(sym, si2lookahead, None if extendedSearch else guide)

        for psis1 in prev1ext:
            guided1 = psis1 in prev1 if prev1 is not None else True
            psi1 = si1src if psis1 is None else psis1
            for psis2 in prev2ext:
                guided2 = psis2 in prev2 if prev2 is not None else True
                psi2 = si2src if psis2 is None else psis2

                if psi1 == si1src and psi2 == si2src:
                    continue
                if psi1.node != psi2.node:
                    continue
                copy = self.copy()
                if psis1 is not None:
                    copy.states1.appendleft(psis1)
                if psis2 is not None:
                    copy.states2.appendleft(psis2)
                if psis1 is not None and psis1.rule.parseIndex + 1 == copy.states1[1].rule.parseIndex:
                    if psis2 is not None and psis2.rule.parseIndex + 1 == copy.states2[1].rule.parseIndex:
                        # Both are reverse transitions; add appropriate
                        # derivation of the corresponding symbol used for
                        # the reverse transition.
                        copy.derivs1.appendleft(Derivation(sym))
                        copy.derivs2.appendleft(Derivation(sym))
                    else:
                        continue
                elif psis2 is not None and psis2.rule.parseIndex + 1 == copy.states2[1].rule.parseIndex:
                    continue
                # At this point, either reverse transition is made on both paths,
                # or reverse production is made on both paths.
                # Now, compute the complexity of the new search state.
                prependSize = (0 if psis1 is None else 1) + (0 if psis2 is None else 1)
                productionSteps = 0 if psis1 is None else countProductionSteps(deque([psis1]), si1src)
                productionSteps += 0 if psis2 is None else countProductionSteps(deque([psis2]), si2src)
                copy.complexity += costs.UNSHIFT_COST * (prependSize - productionSteps)
                copy.complexity += costs.PRODUCTION_COST * productionSteps
                if not guided1 or not guided2:
                    copy.complexity += costs.EXTENDED_COST
                out.append(copy)

        return out

    def reduce1(self, nextSym: Optional[Symbol], item1: StateItem) -> List['Configuration']:
        states = self.states1
        derivs = self.derivs1
        sSize = len(states)
        item = states[-1].rule
        if not item.indexAtEnd():
            raise HermesError("Configuration.reduce1() Cannot reduce item without dot at end")
        out: List[Configuration] = []

        symbolSet = {nextSym} if nextSym is not None else item.lookAhead

        if not intersectSet(item.lookAhead, symbolSet):
            return out

        lhs = item.rule.nonterm
        ruleLen = len(item)
        dSize = len(derivs)

        deriv = Derivation(lhs, list(sliceDeque(self.derivs1, dSize - ruleLen, dSize)))
        if self.reduceDepth == 0:
            # We are reducing the reduce conflict item.
            # Add a dot for visual inspection of the resulting counterexample.
            if deriv.deriv is not None:
                deriv.deriv.append(DOT)

        derivs = sliceDeque(derivs, 0, dSize - ruleLen)
        derivs.append(deriv)
        if sSize == ruleLen + 1:
            # The head StateItem is a production item, so we need to prepend
            # with possible source StateItems.
            prev = states[0].reverseProduction(symbolSet)
            for psis in prev:
                copy = self.copy()
                copy.derivs1 = derivs
                copy.states1 = sliceDeque(self.states1, 0, sSize - ruleLen - 1)
                copy.states1.extendleft(reversed(psis))
                dst = copy.states1[-1].transItem
                if dst is None:
                    raise RuntimeError("Configuration.reduce1() Transition item not setup")
                copy.states1.append(dst)

                pSteps = countProductionSteps(copy.states1, states[0])
                copy.complexity += costs.UNSHIFT_COST * (len(copy.states1) - pSteps)
                copy.complexity += costs.PRODUCTION_COST * pSteps
                if copy.reduceDepth == 0:
                    copy.reduceDepth -= 1
                out.append(copy)
        else:
            copy = self.copy()
            copy.derivs1 = derivs
            copy.states1 = sliceDeque(self.states1, 0, sSize - ruleLen - 1)
            # copy.states1.append(StateItem.FWD_TRANS[copy.states1[-1]][lhs])
            dst = copy.states1[-1].transItem
            if dst is None:
                raise RuntimeError("Configuration.reduce1() Transition item not setup")
            copy.states1.append(dst)
            copy.complexity += costs.REDUCE_COST
            if copy.reduceDepth == 0:
                copy.reduceDepth -= 1
            out.append(copy)

        # Transition on nullable symbols
        finalizedResult = []
        for ss in out:
            nextS = ss.states1[-1]
            derivs1 = deque()
            states1 = deque()
            nullableClosure(nextS.rule, nextS.rule.parseIndex, nextS, states1, derivs1)
            finalizedResult.append(ss)
            for i in range(1, len(derivs1)):
                subderivs1 = sliceDeque(derivs1, 0, i)
                substates1 = sliceDeque(states1, 0, i)
                copy = ss.copy()
                copy.derivs1.extend(subderivs1)
                copy.states1.extend(substates1)
                finalizedResult.append(copy)

        return finalizedResult

    def reduce2(self, nextSym: Optional[Symbol], item2: StateItem) -> List['Configuration']:
        states = self.states2
        derivs = self.derivs2
        item = states[-1].rule
        sSize = len(states)
        if not item.indexAtEnd():
            raise HermesError("Configuration.reduce2() Cannot reduce item without dot at end")
        out: List[Configuration] = []
        symbolSet = item.lookAhead if nextSym is None else {nextSym}
        if len(symbolSet & item.lookAhead) == 0:
            return out
        lhs = item.rule.nonterm
        ruleLen = len(item)
        dSize = len(derivs)
        deriv = Derivation(item.rule.nonterm, list(sliceDeque(derivs, dSize - ruleLen, dSize)))
        if self.shiftDepth == 0:
            # We are reducing the shift conflict item (for shift/reduce conflict),
            # or the other reduce conflict item (for reduce/reduce conflict).
            # Add a dot for visual inspection of the resulting counterexample.
            if deriv.deriv is not None:
                deriv.deriv.append(DOT)

        derivs = sliceDeque(derivs, 0, dSize - ruleLen)
        derivs.append(deriv)
        if sSize == ruleLen + 1:
            # The head StateItem is a production item, so we need to prepend
            # with possible source StateItems.
            prev = states[0].reverseProduction(symbolSet)
            for psis in prev:
                copy = self.copy()
                copy.derivs2 = derivs
                copy.states2 = sliceDeque(states, 0, sSize - ruleLen - 1)
                copy.states2.extendleft(reversed(psis))
                dst = copy.states2[-1].transItem
                if dst is None:
                    raise RuntimeError("Configuration.reduce2() Transition item not setup")
                copy.states2.append(dst)

                pSteps = countProductionSteps(copy.states2, states[0])
                copy.complexity += costs.SHIFT_COST * (len(copy.states2) - pSteps)
                copy.complexity += costs.PRODUCTION_COST * pSteps
                if copy.shiftDepth >= 0:
                    copy.shiftDepth -= 1
                out.append(copy)
        else:
            copy = self.copy()
            copy.derivs2 = derivs
            copy.states2 = sliceDeque(states, 0, sSize - ruleLen - 1)
            dst = copy.states2[-1].transItem
            if dst is None:
                raise RuntimeError("Configuration.reduce2() Transition item not setup")
            copy.states2.append(dst)
            copy.complexity += costs.REDUCE_COST
            if copy.shiftDepth >= 0:
                copy.shiftDepth -= 1
            out.append(copy)
        # transition on nullable symbols
        finalizedResult = []
        for ss in out:
            nextS = ss.states2[-1]
            derivs2: Deque[Derivation] = deque()
            states2: Deque[StateItem] = deque()
            nullableClosure(nextS.rule, nextS.rule.parseIndex, nextS, states2, derivs2)
            finalizedResult.append(ss)
            for i in range(1, len(derivs2)):
                subderivs2 = sliceDeque(derivs2, 0, i)
                substates2 = sliceDeque(states2, 0, i)
                copy = ss.copy()
                copy.derivs2.extend(subderivs2)
                copy.states2.extend(substates2)
                finalizedResult.append(copy)

        return finalizedResult

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Configuration):
            return False
        # TODO make sure this checks the list correctly
        return self.states1 == value.states1 and self.states2 == value.states2

    def __hash__(self) -> int:
        return hash((tuple(self.states1), tuple(self.states2)))


class ComplexityConfiguration:
    """
    set of configurations with the same complexity
    """

    def __init__(self, complexity: int) -> None:
        self.complexity = complexity
        self.configs: Set[Configuration] = set()

    def __lt__(self, other: 'ComplexityConfiguration') -> bool:
        return self.complexity < other.complexity

    def add(self, state: Configuration):
        self.configs.add(state)

    def print(self):
        # TODO remove
        print("FCSS, Complexity:", self.complexity)
        for idx, ss in enumerate(self.configs):
            print("Search State", idx)
            print("States1:")
            for si in ss.states1:
                print("   ", si)
            print("States2:")
            for si in ss.states2:
                print("   ", si)

            print("Derivs1:")
            for d in ss.derivs1:
                print("   ", d)
            print("Derivs2:")
            for d in ss.derivs2:
                print("   ", d)


class ComplexityQueue:
    """
    Priority queue of ComplexityConfigurations
    """

    def __init__(self) -> None:
        self._q = []

    def push(self, state: ComplexityConfiguration):
        heapq.heappush(self._q, (state.complexity, state))

    def pop(self) -> ComplexityConfiguration:
        return heapq.heappop(self._q)[1]

    def __len__(self) -> int:
        return len(self._q)
