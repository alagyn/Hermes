from .derivation import Derivation


class CounterExample:

    def __init__(
        self, d1: Derivation, d2: Derivation, unifying: bool, isShiftReduce: bool, timeout: bool = False
    ) -> None:
        self.d1 = d1
        self.d2 = d2
        self.unifying = unifying
        self.timeout = timeout
        self.isShiftReduce = isShiftReduce

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
