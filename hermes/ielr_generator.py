from typing import List

from hermes.lalr1_automata import LALR1Automata, Node


class IELRAutomata:

    def __init__(self, lalr: LALR1Automata) -> None:
        self.lalr = lalr

        self.lalr1_isocores: List[Node] = []
        self.isocores_nexts: List[Node] = []
        self.lookaheads_recomputed: List[bool] = []

    def split_states(self):
        for node in self.lalr.nodes:
            self.lalr1_isocores.append(node)
            self.isocores_nexts.append(node)
            self.lookaheads_recomputed.append(False)

        for node in self.lalr.nodes:
            for symbol, nextNode in node.trans.items():
                self.compute_state(node, nextNode)

    def propagate_lookaheads(self, s: Node, SPrime: Node):
        pass  # TODO

    def is_compatible(self, i: Node, K) -> bool:
        return False  # TODO

    def compute_state(self, s: Node, sPrime: Node):
        K = self.propagate_lookaheads(s, sPrime)
        found = False
        i = s
        while True:
            if self.is_compatible(i, K):
                found = True
                break
            nextIso = self.isocores_nexts[i.id]
            if nextIso == sPrime:
                break
            i = nextIso
        if not found:
            pass  # TODO
        elif not self.lookaheads_recomputed[i.id]:
            pass  # TODO
        else:
            pass  # TODO
