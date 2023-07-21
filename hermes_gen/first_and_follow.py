from typing import Dict

from hermes_gen.ebnf_grammar import Grammar
from hermes_gen.consts import EMPTY, END


class FirstAndFollow:

    def __init__(self, grammar: Grammar) -> None:
        self.first: Dict[str, set[str]] = {}
        for symbol in grammar.symbols:
            self.first[symbol] = set()
            if symbol in grammar.nulls:
                self.first[symbol].add(EMPTY)

        # Initialize the .irst set to contain the terminals
        for term in grammar.terminals:
            self.first[term] = set([term])

        changed = True
        while changed:
            changed = False
            for rule in grammar.rules:
                curSet = self.first[rule.nonterm].copy()

                nullable = True
                for symbol in rule.symbols:
                    curSet.update(self.first[symbol])
                    if symbol not in grammar.nulls:
                        nullable = False
                        break

                if nullable:
                    curSet.add(EMPTY)

                if curSet > self.first[rule.nonterm]:
                    self.first[rule.nonterm] = curSet
                    changed = True
            # End for rule
        # End while changed

        self.follow: Dict[str, set[str]] = {
            x.nonterm: set()
            for x in grammar.rules
        }
        for x in grammar.terminals:
            self.follow[x] = set()

        self.follow[grammar.startSymbol] = {END}

        changed = True
        while changed:
            changed = False
            for rule in grammar.rules:
                left = self.follow[rule.nonterm]
                # True if the previous symbol had EMPTy in their first set
                lastEmpty = True
                # Iterate backwards so to keep track of when the next symbol can be empty
                for i in reversed(range(len(rule.symbols))):
                    curSymbol = rule.symbols[i]
                    if curSymbol == EMPTY:
                        break

                    if lastEmpty:
                        right = self.follow[curSymbol]
                        new = left.union(right)
                        if new > right:
                            self.follow[curSymbol] = new
                            changed = True
                        lastEmpty = EMPTY in self.first[curSymbol]
                    if i > 0:
                        prior = rule.symbols[i - 1]
                        curFirst = self.first[curSymbol].difference({EMPTY})
                        priorFollow = self.follow[prior]
                        new = priorFollow.union(curFirst)
                        if new > priorFollow:
                            self.follow[prior] = new
                            changed = True
                # End for symbols
            # End for rules
        # End while changed

        for x in grammar.terminals:
            del self.follow[x]
