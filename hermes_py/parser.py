from typing import Optional, Any, List, Callable
import re
import io
import os


class TerminalDef:

    def __init__(self, id: int, regex: bytes):
        self.id = id
        self.regex = regex


class Reduction:

    def __init__(self, numPos: int, nonterm: int):
        self.numPos = numPos
        self.nonterm = nonterm


E = 0
S = 1
R = 2
G = 3


class ParseAction:

    def __init__(self, action: int = E, state: int = 0) -> None:
        self.action = action
        self.state = state


class Location:

    def __init__(self) -> None:
        self.lineStart = 0
        self.charStart = 0
        self.lineEnd = 0
        self.charEnd = 0


class ParseToken:

    def __init__(self) -> None:
        self.symbol = 0
        self.text = ""
        self.loc = Location()


class StackItem:

    def __init__(self, state: int, symbol: int, loc: Location) -> None:
        self.state = state
        self.symbol = symbol
        self.loc = loc
        self.token: Optional[str] = None
        self.nt: Optional[Any] = None


ReductionFunc = Callable[[List[StackItem]], int]


class _Terminal:

    def __init__(self, t: TerminalDef) -> None:
        self.id = t.id
        self.regex = re.compile(t.regex)


CARRIAGE_RETURN = b'\x0D'
LINE_FEED = b'\x0A'


class _Scanner:

    def __init__(self, f: io.RawIOBase, terminals: List[TerminalDef], numSymbols: int) -> None:
        self.terminals = [_Terminal(x) for x in terminals]
        self.f = io.BufferedReader(f)

        self.lineNum = 1
        self.charNum = 1
        self.lastLineLength = 0
        self.symbolEOF = numSymbols - 2
        self.symbolIGNORE = numSymbols - 1

    def nextToken(self) -> ParseToken:
        out = self._nextToken()
        while out.symbol == self.symbolIGNORE:
            out = self._nextToken()
        return out

    def eof(self) -> bool:
        return len(self.f.peek(1)) == 0

    def get(self) -> bytes:
        out = self.f.read(1)
        # Handle window/mac line endings
        if out == CARRIAGE_RETURN:
            out = self.f.read(1)
            # Line-feed
            if out != LINE_FEED:
                # if it wasn't actually \r\n, unget
                self.unget()
                # force to \n for the next if block
                out = LINE_FEED

        if out == LINE_FEED:
            self.lineNum += 1
            self.lastLineLength = self.charNum
            self.charNum = 1
        else:
            self.charNum += 1

        return out

    def unget(self):
        # TODO might need to test if this is slow
        self.f.seek(-1, os.SEEK_CUR)
        if self.f.peek(1) == LINE_FEED:
            self.lineNum -= 1
            self.charNum = self.lastLineLength
        else:
            self.charNum -= 1

    def _nextToken(self) -> ParseToken:
        out = ParseToken()
        out.loc.lineStart = self.lineNum
        out.loc.charStart = self.charNum

        # flag for if we have started having matches
        foundMatch = False
        foundPartial = True
        while not self.eof():
            nextChar = self.get()

        return out


class Parser:

    def __init__(
        self,
        symbolLookup: List[int],
        terminals: List[TerminalDef],
        reductions: List[Reduction],
        reductionFuncs: List[ReductionFunc],
        parseTable: List[List[ParseAction]]
    ) -> None:
        self._symbolLookup = symbolLookup
        self._terminals = terminals
        self._reductions = reductions
        self._reductionFuncs = reductionFuncs
        self._parseTable = parseTable

    def parse(self, f: io.RawIOBase) -> Any:
        scanner = _Scanner(f, self._terminals, len(self._symbolLookup))
