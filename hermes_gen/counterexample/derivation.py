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

    def prettyPrint(self) -> str:
        if self.deriv is None:
            return self.symbol.name

        out = []
        for d in self.deriv:
            x = d.prettyPrint()
            out.append(x)

        return " ".join(out)

    def __str__(self) -> str:
        out = [self.symbol.name]

        if self.deriv is not None:
            out.append("= [")
            for d in self.deriv:
                out.append(str(d))
            out.append("]")

        return " ".join(out)

    def __repr__(self) -> str:
        return str(self)


_DOT = Symbol(".", "", False)
del Symbol._SYMBOL_MAP['.']

DOT = Derivation(_DOT)
