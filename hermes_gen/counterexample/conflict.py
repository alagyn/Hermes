from hermes_gen.grammar import Symbol
from hermes_gen.lalr1_automata import Node, AnnotRule


class Conflict:

    def __init__(self, node: Node, symbol: Symbol, first: AnnotRule, second: AnnotRule) -> None:
        self.node = node
        self.symbol = symbol
        # If this is a S/R conflict, we want the R to be item 1
        # otherwise, it doesn't matter
        if first.indexAtEnd():
            # our first rule is a reduce rule, check the second
            if second.indexAtEnd():
                # we have a R/R conflict
                self.isShiftReduce = False
            else:
                # we have a S/R
                self.isShiftReduce = True

            # order doesn't matter if R/R, but we def want item 1
            # to be a reduce item
            self.rule1 = first
            self.rule2 = second
        elif second.indexAtEnd():
            # out second rule is a reduce, but the first is a shift
            self.isShiftReduce = True
            self.rule1 = second
            self.rule2 = first
        else:
            # shouldn't ever reach here?
            # S/S conflicts are impossible
            raise RuntimeError("generate_counterexample() Expected at least one reduce rule")

    def __str__(self) -> str:
        message = [f"Warning: conflict detected in {self.node}"]
        message.append(f"  Conflict Type: {'Shift-Reduce' if self.isShiftReduce else 'Reduce-Reduce'}")
        message.append(f"  Symbol: {self.symbol}")
        if self.isShiftReduce:
            message.append(f'  Reduce: {self.rule1}')
            message.append(f'   Shift: {self.rule2}')
        else:
            message.append(f'  Reduce 1: {self.rule1}')
            message.append(f'  Reduce 2: {self.rule2}')
        return "\n".join(message)
