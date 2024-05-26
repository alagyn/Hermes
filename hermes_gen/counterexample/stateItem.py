from typing import List, Optional, Set, Dict, Tuple
from collections import defaultdict

from hermes_gen.lalr1_automata import Node, AnnotRule, LALR1Automata
from hermes_gen.grammar import Symbol


class StateItem:
    # Map a state item to the corresponding state item after a shift action is taken
    FWD_TRANS: Dict['StateItem', Dict[Symbol, 'StateItem']] = defaultdict(dict)
    # Same, but in reverse. There can maybe be more than on SI that shifts to any particular SI
    REV_TRANS: Dict['StateItem', Dict[Symbol, Set['StateItem']]] = defaultdict(dict)

    # Map a state item to its possible productions
    FWD_PROD: Dict['StateItem', Set['StateItem']] = defaultdict(set)
    REV_PROD: Dict[Node, Dict[Symbol, Set['StateItem']]] = defaultdict(dict)

    # lookup map for a specific state item with the given state and rule
    STATE_ITEM_LOOKUP: Dict[Tuple[Node, AnnotRule], 'StateItem'] = {}

    # Reference to automata
    AUTOMATA: LALR1Automata = None  # type: ignore

    @classmethod
    def initLookups(cls, automata: LALR1Automata) -> None:
        cls.AUTOMATA = automata

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

                    cls.FWD_TRANS[srcSI][nextSymbol] = dstSI

                    try:
                        cls.REV_TRANS[dstSI][nextSymbol].add(srcSI)
                    except KeyError:
                        revSet = set()
                        revSet.add(srcSI)
                        cls.REV_TRANS[dstSI][nextSymbol] = revSet
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
            revProd = cls.REV_PROD[src]

            for rule in src.rules:
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
                state = cls.getStateItem(src, rule)
                # union the set
                cls.FWD_PROD[state] |= closures

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

    def __str__(self) -> str:
        return f'{str(self.node)} {str(self.rule)}'

    def __repr__(self) -> str:
        return self.__str__()

    def reverseTransition(self, symbol: Symbol, lookahead: Set[Symbol],
                          guide: Optional[Set[Node]]) -> List[Optional['StateItem']]:
        """
        Compute a set of StateItems that can make a transition on the given
        symbol to this StateItem such that the resulting possible lookahead
        symbols are as given.
        """

        ss = SearchState([self], lookahead)

        out: List[Optional[StateItem]] = [None]
        if self.rule.parseIndex > 0:
            prevs = self.REV_TRANS[self][symbol]
            if len(prevs) == 0:
                return out

            for prev in prevs:
                if guide is not None and prev.node not in guide:
                    continue
                # check if the lookaheads don't intersect
                if len(lookahead & prev.rule.lookAhead) == 0:
                    continue

                out.append(prev)
            return out

        # Consider items in the same state that might use this production.
        # TODO is this necessary? This just discards the lookaheads...
        # can maybe eliminate SearchState?
        for x in ss.reverseProduction():
            out.append(x.items[0])
        return out

    def reverseProduction(self, lookahead: Set[Symbol]) -> List[List['StateItem']]:
        out = []

        for ss in SearchState([self], lookahead).reverseProduction():
            out.append(ss.items[:-1])

        return out


class SearchState:

    def __init__(self, stateItems: List[StateItem], lookahead: Set[Symbol]) -> None:
        self.items = stateItems
        self.lookahead = lookahead

    def reverseProduction(self) -> List['SearchState']:
        out: List[SearchState] = []

        si = self.items[0]
        revProd = StateItem.REV_PROD[si.node]
        if len(revProd) == 0:
            return out

        lhs = si.rule.rule.nonterm
        try:
            prevs = revProd[lhs]
        except KeyError:
            return out

        for prev in prevs:
            if not self.productionAllowed(prev):
                continue
            prevLen = len(prev.rule.rule.symbols)
            prevPos = prev.rule.parseIndex + 1
            prevLookahead = prev.rule.lookAhead
            nextLookahead: Set[Symbol] = set()
            # reduce item
            if (prevPos == prevLen):
                # check for LA intersection
                if len(prevLookahead & si.rule.lookAhead) == 0:
                    continue
                nextLookahead = prevLookahead & self.lookahead
            # shift item
            else:
                if len(self.lookahead) > 0:
                    # Check that lookahead is compatible with the first
                    # possible symbols in the rest of the production.
                    # Alternatively, if the rest of the production is
                    # nullable, the lookahead must be compatible with
                    # the lookahead of the corresponding item.
                    applicable = False
                    nullable = True
                    i = prevPos
                    while not applicable and nullable and i < prevLen:
                        nextSym = prev.rule.rule.symbols[i]
                        if nextSym.isTerminal:
                            applicable = nextSym in self.lookahead
                            nullable = False
                        else:
                            applicable = len(nextSym.first & self.lookahead) > 0
                            if not applicable:
                                nullable = nextSym.nullable
                        i += 1
                    if not applicable and not nullable:
                        continue
                nextLookahead = prevLookahead
            out.append(SearchState([prev], nextLookahead))

        return out

    def productionAllowed(self, prev: 'StateItem') -> bool:
        # TODO this is supposed to use precendence and associativity, which Hermes doesn't do yet
        return True
