from typing import Optional, List

from ..grammar import Symbol


class Derivation:

    def __init__(self, symbol: Symbol, deriv: Optional[List['Derivation']] = None) -> None:
        self.symbol = symbol
        self.deriv = deriv

    def __eq__(self, other) -> bool:
        if not isinstance(other, Derivation):
            raise NotImplementedError()

        return self.symbol == other.symbol

    def __hash__(self):
        return hash(self.symbol)
