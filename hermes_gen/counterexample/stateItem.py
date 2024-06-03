from typing import List, Optional, Set, Dict, Tuple
from collections import defaultdict

from hermes_gen.lalr1_automata import Node, AnnotRule, LALR1Automata
from hermes_gen.grammar import Symbol


def intersect(terminal: Symbol, syms: Optional[Set[Symbol]]) -> bool:
    if syms is None:
        return True
    for sym in syms:
        if sym == terminal:
            return True
        elif not sym.isTerminal and terminal in sym.first:
            return True

    return False


def intersectSet(terminals: Set[Symbol], syms: Optional[Set[Symbol]]) -> bool:
    if syms is None:
        return True
    for sym in syms:
        if sym in terminals:
            return True
        elif not sym.isTerminal and len(sym.first & terminals) > 0:
            return True
    return False


class StateItem:

    # lookup map for a specific state item with the given state and rule
    STATE_ITEM_LOOKUP: Dict[Tuple[Node, AnnotRule], 'StateItem'] = {}

    # Reference to automata
    AUTOMATA: LALR1Automata = None  # type: ignore

    @classmethod
    def initLookups(cls, automata: LALR1Automata) -> None:
        cls.AUTOMATA = automata

        cls.STATE_ITEM_LOOKUP.clear()

        # Compute transition maps

        for src in automata.nodes:
            for rule in src.rules:
                if rule.indexAtEnd():
                    # ignore reduction rules
                    continue
                nextSymbol = rule.nextSymbol()
                expParseIndex = rule.parseIndex + 1
                dst = src.trans[nextSymbol]
                for dstRule in dst.rules:
                    # find the matching rule with the expected dot
                    if dstRule.rule != rule.rule or dstRule.parseIndex != expParseIndex:
                        continue

                    srcSI = cls.getStateItem(src, rule)
                    dstSI = cls.getStateItem(dst, dstRule)

                    srcSI.transSymbol = nextSymbol
                    srcSI.transItem = dstSI

                    dstSI.revTrans[nextSymbol].add(srcSI)

                    break

        # Compute production maps
        for src in automata.nodes:
            # closureMap records all items with dot at the beginning of the
            # right-hand side in this state. In other words, the items
            # recorded are the productions added to this state by taking closure.
            closureMap: Dict[Symbol, Set[StateItem]] = defaultdict(set)
            for rule in src.rules:
                if rule.parseIndex == 0:
                    lhs = rule.rule.nonterm
                    closureMap[lhs].add(cls.getStateItem(src, rule))

            # rev prods for this node
            revProd: Dict[Symbol, Set['StateItem']] = {}

            for rule in src.rules:
                # always set the revProd map
                state = cls.getStateItem(src, rule)
                state.revProd = revProd
                # Avoid reduce items, which cannot make a production step.
                if rule.indexAtEnd():
                    continue
                symbol = rule.nextSymbol()
                # if next symbol is a terminal, cannot make a production step
                if symbol.isTerminal:
                    continue
                try:
                    closures = closureMap[symbol]
                except KeyError:
                    continue

                # union the set
                state.fwdProd.update(closures)

                try:
                    revItems = revProd[symbol]
                except KeyError:
                    revItems = set()
                    revProd[symbol] = revItems

                revItems.add(state)

    @classmethod
    def getStateItem(cls, node: Node, rule: AnnotRule) -> 'StateItem':
        try:
            return cls.STATE_ITEM_LOOKUP[(node, rule)]
        except KeyError:
            out = StateItem(node, rule)
            cls.STATE_ITEM_LOOKUP[(node, rule)] = out
            return out

    def __init__(self, node: Node, rule: AnnotRule) -> None:
        self.node = node
        self.rule = rule
        self.transSymbol: Optional[Symbol] = None if rule.indexAtEnd() else rule.nextSymbol()
        self.transItem: Optional[StateItem] = None
        self.revTrans: Dict[Symbol, Set[StateItem]] = defaultdict(set)
        self.fwdProd: Set[StateItem] = set()
        self.revProd: Dict[Symbol, Set[StateItem]] = {}

        self._name = f'n{node.id}r{node.rules.index(rule)}'

    def __str__(self) -> str:
        return f'{str(self.node)} {str(self.rule)}'

    def __repr__(self) -> str:
        return self._name

    def reverseTransition(self, symbol: Symbol, lookahead: Set[Symbol],
                          guide: Optional[Set[Node]]) -> List[Optional['StateItem']]:
        """
        Compute a set of StateItems that can make a transition on the given
        symbol to this StateItem such that the resulting possible lookahead
        symbols are as given.
        """

        ss = _SearchState([self], lookahead)

        out: List[Optional[StateItem]] = [None]
        if self.rule.parseIndex > 0:
            prevs = self.revTrans[symbol]
            if len(prevs) == 0:
                return out

            for prev in prevs:
                if guide is not None and prev.node not in guide:
                    continue
                # check if the lookaheads don't intersect
                if not intersectSet(prev.rule.lookAhead, ss.lookahead):
                    continue

                out.append(prev)
            return out

        # Consider items in the same state that might use this production.
        for x in ss.reverseProduction():
            out.append(x.items[0])
        return out

    def reverseProduction(self, lookahead: Set[Symbol]) -> List[List['StateItem']]:
        out = []

        for ss in _SearchState([self], lookahead).reverseProduction():
            out.append(ss.items[:-1])

        return out


class _SearchState:

    def __init__(self, stateItems: List[StateItem], lookahead: Optional[Set[Symbol]]) -> None:
        self.items = stateItems
        self.lookahead = lookahead

    def reverseProduction(self) -> List['_SearchState']:
        out: List[_SearchState] = []

        si = self.items[0]
        revProd = si.revProd
        if len(revProd) == 0:
            return out

        lhs = si.rule.rule.nonterm
        try:
            prevs = revProd[lhs]
        except KeyError:
            return out

        for prev in prevs:
            if not productionAllowed(prev, si):
                continue
            prevLen = len(prev.rule)
            prevPos = prev.rule.parseIndex + 1
            prevLookahead = prev.rule.lookAhead
            nextLookahead: Set[Symbol] = set()
            # reduce item
            if (prevPos == prevLen):
                # check for LA intersection
                if not intersectSet(prevLookahead, self.lookahead):
                    continue
                if self.lookahead is not None:
                    nextLookahead = prevLookahead & self.lookahead
            # shift item
            else:
                if self.lookahead is not None:
                    # Check that lookahead is compatible with the first
                    # possible symbols in the rest of the production.
                    # Alternatively, if the rest of the production is
                    # nullable, the lookahead must be compatible with
                    # the lookahead of the corresponding item.
                    applicable = False
                    nullable = True
                    i = prevPos
                    while not applicable and nullable and i < prevLen:
                        nextSym = prev.rule[i]
                        if nextSym.isTerminal:
                            applicable = intersect(nextSym, self.lookahead)
                            nullable = False
                        else:
                            applicable = intersectSet(nextSym.first, self.lookahead)
                            if not applicable:
                                nullable = nextSym.nullable
                        i += 1
                    if not applicable and not nullable:
                        continue
                nextLookahead = prevLookahead
            out.append(_SearchState([prev, *self.items], nextLookahead))

        return out


def productionAllowed(prod: StateItem, prev: StateItem) -> bool:
    # TODO this is supposed to use precendence and associativity, which Hermes doesn't do yet
    return True
