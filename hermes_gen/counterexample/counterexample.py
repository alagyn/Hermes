from .derivation import Derivation


class CounterExample:

    def __init__(self, d1: Derivation, d2: Derivation, unifying: bool, timeout: bool = False) -> None:
        self.d1 = d1
        self.d2 = d2
        self.unifying = unifying
        self.timeout = timeout
