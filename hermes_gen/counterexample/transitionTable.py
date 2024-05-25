from typing import Deque, List, Dict, Set, Tuple
from collections import defaultdict

from .stateItem import StateItem
from ..lalr1_automata import LALR1Automata, Node, AnnotRule

# Map a state item to the corresponding state item after a shift action is taken
TransMap = Dict[StateItem, Dict[str, StateItem]]
# Same, but in reverse. There can maybe be more than on SI that shifts to any particular SI
RevTransMap = Dict[StateItem, Dict[str, Set[StateItem]]]

# Map a state item to its possible productions
ProdMap = Dict[StateItem, Set[StateItem]]
RevProdMap = Dict[Node, Dict[str, Set[StateItem]]]

# lookup map for a specific state item with the given state and rule
StateItemLookup = Dict[Tuple[Node, AnnotRule], StateItem]


class TransitionTable:

    def __init__(self, automata: LALR1Automata) -> None:
        self.stateItemLookup: StateItemLookup = {}

        # Compute transition maps
        self.fwd: TransMap = defaultdict(dict)
        self.rev: RevTransMap = defaultdict(dict)

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

                    srcSI = self.getStateItem(src, rule)
                    dstSI = self.getStateItem(dst, dstRule)

                    self.fwd[srcSI][nextSymbol] = dstSI

                    try:
                        self.rev[dstSI][nextSymbol].add(srcSI)
                    except KeyError:
                        revSet = set()
                        revSet.add(srcSI)
                        self.rev[dstSI][nextSymbol] = revSet
                    break

        # Compute production maps
        self.prods: ProdMap = defaultdict(set)
        self.revProds: RevProdMap = defaultdict(dict)

        for src in automata.nodes:
            # closureMap records all items with dot at the beginning of the
            # right-hand side in this state. In other words, the items
            # recorded are the productions added to this state by taking closure.
            closureMap: Dict[str, Set[StateItem]] = defaultdict(set)
            for rule in src.rules:
                if rule.parseIndex == 0:
                    lhs = rule.rule.nonterm
                    closureMap[lhs].add(self.getStateItem(src, rule))

            # rev prods for this node
            revProd = self.revProds[src]

            for rule in src.rules:
                # Avoid reduce items, which cannot make a production step.
                if rule.indexAtEnd():
                    continue
                symbol = rule.nextSymbol()
                # if next symbol is a terminal, cannot make a production step
                if symbol in automata.grammar.terminals:
                    continue
                try:
                    closures = closureMap[symbol]
                except KeyError:
                    continue
                state = self.getStateItem(src, rule)
                # union the set
                self.prods[state] |= closures

                try:
                    revItems = revProd[symbol]
                except KeyError:
                    revItems = set()
                    revProd[symbol] = revItems

                revItems.add(state)

    def getStateItem(self, node: Node, rule: AnnotRule) -> StateItem:
        try:
            return self.stateItemLookup[(node, rule)]
        except KeyError:
            out = StateItem(node, rule)
            self.stateItemLookup[(node, rule)] = out
            return out
