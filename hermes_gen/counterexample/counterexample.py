from .derivation import Derivation
from .conflict import Conflict


class CounterExample:

    def __init__(
        self, conflict: Conflict, d1: Derivation, d2: Derivation, unifying: bool, timeout: bool = False
    ) -> None:
        self.c = conflict
        self.d1 = d1
        self.d2 = d2
        self.unifying = unifying
        self.timeout = timeout
        self.isShiftReduce = conflict.isShiftReduce

    def nonTerminal(self) -> str:
        return self.d1.symbol.name

    def prettyExample1(self) -> str:
        return self.d1.prettyPrint()

    def prettyExample2(self) -> str:
        return self.d2.prettyPrint()

    def example1(self) -> str:
        return str(self.d1)

    def example2(self) -> str:
        return str(self.d2)

    def prettyPrint(self, color: bool) -> str:
        if color:
            y = "\033[1;33m"
            off = "\033[0m"
        else:
            y = ""
            off = ""
        message = [
            f'{y}Warning: conflict detected in {self.c.node}{off}',
        ]

        message.append(f"  Conflict Type: {'Shift-Reduce' if self.isShiftReduce else 'Reduce-Reduce'}")

        if self.isShiftReduce:
            if self.c.rule1.indexAtEnd():
                message.append(f"  Reduce: {self.c.rule1}")
                message.append(f'   Shift: {self.c.rule2}')
            else:
                message.append(f"  Reduce: {self.c.rule2}")
                message.append(f'   Shift: {self.c.rule1}')
        else:
            message.append(f'  Reduce 1: {self.c.rule1}')
            message.append(f'  Reduce 2: {self.c.rule2}')

        message.append("")

        if self.unifying:
            message.append("  Unifying example found")
            message.append(f"  Ambiguity for nonterminal: {self.nonTerminal()}")
            message.append("  Example:")
            message.append(f'    {self.prettyExample1()}')

            message.append("")

            if self.isShiftReduce:
                message.append("  Derivation using reduction:")
            else:
                message.append("  Derivation using reduction 1:")
            message.append(f'    {self.example1()}')

            if self.isShiftReduce:
                message.append("  Derivation using shift:")
            else:
                message.append("  Derivation using reduction 2:")

            message.append(f'    {self.example2()}')
        else:
            message.append("  No Unifying example found")

            if self.isShiftReduce:
                message.append("  Example using reduction:")
            else:
                message.append("  Example using reduction 1:")
            message.append(f'    {self.prettyExample1()}')
            message.append("  Derivation:")
            message.append(f'    {self.example1()}')

            message.append("")

            if self.isShiftReduce:
                message.append("  Example using shift:")
            else:
                message.append("  Example using reduction 2:")
            message.append(f'    {self.prettyExample2()}')
            message.append("  Derivation:")
            message.append(f'    {self.example2()}')
        return "\n".join(message)
