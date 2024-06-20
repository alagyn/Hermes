from typing import Optional, List
from io import StringIO

from ..grammar import Symbol

COLORS = [
    "\x1B[91m",
    "\x1B[92m",
    "\x1B[93m",
    "\x1B[95m",
    "\x1B[96m",
    "\x1B[94m",
    "\x1B[97m",
]


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

    def _prettyTree(self, color: bool, lines: List[StringIO], lens: List[int], depth: int):
        curLine = lines[depth]

        curLine.write(self.symbol.name)
        curLine.write(" ")

        curLen = lens[depth]

        actualLen = curLen + len(self.symbol.name) + 1

        if self.deriv is not None:
            if len(lines) == depth + 1:
                nextLine = StringIO()
                if color:
                    nextLine.write(COLORS[depth + 1 % len(COLORS)])
                for _ in range(curLen):
                    nextLine.write(" ")
                lines.append(nextLine)
                lens.append(curLen)

            nextLine = lines[depth + 1]
            nextLen = lens[depth + 1]
            if nextLen < curLen:
                for _ in range(curLen - nextLen):
                    nextLine.write(" ")
                lens[depth + 1] = curLen

            nextLine.write("↳ ")
            lens[depth + 1] += 2
            for d in self.deriv:
                d._prettyTree(color, lines, lens, depth + 1)
                if lens[depth + 1] > actualLen:
                    for _ in range(lens[depth + 1] - actualLen):
                        curLine.write(" ")
                    actualLen = lens[depth + 1]

        lens[depth] = actualLen

    def prettyTree(self, color: bool) -> str:
        if self.deriv is None:
            return self.symbol.name

        lines: List[StringIO] = [StringIO()]
        if color:
            lines[0].write(COLORS[0])
        lines[0].write("  ")

        lens = [2]

        self._prettyTree(color, lines, lens, 0)

        out = StringIO()
        for s in lines:
            out.write(s.getvalue())
            out.write("\n")
        if color:
            out.write("\x1B[0m")
        return out.getvalue()

    def __str__(self) -> str:
        out = [self.symbol.name]

        if self.deriv is not None:
            out.append(" = [")
            first = True
            for d in self.deriv:
                if first:
                    first = False
                else:
                    out.append(" ")
                out.append(str(d))

            out.append("]")

        return "".join(out)

    def __repr__(self) -> str:
        return str(self)


_DOT = Symbol("•", "", False)
del Symbol._SYMBOL_MAP['•']

DOT = Derivation(_DOT)
