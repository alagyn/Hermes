from typing import List, Dict, Set, Tuple, Iterable
from collections import deque, defaultdict
import re
import os

from hermes_gen.errors import HermesError
from hermes_gen.consts import ARG_VECTOR, EMPTY, END, START
from hermes_gen.directives import Directive

_EMPTY_STR = "EMPTY"


class Symbol:
    _ID_GEN = 0
    _SYMBOL_MAP: Dict[str, 'Symbol'] = {}

    EMPTY_SYMBOL: 'Symbol' = None  # type: ignore
    END_SYMBOL: 'Symbol' = None  # type: ignore

    @classmethod
    def reset(cls):
        cls._ID_GEN = 0
        cls._SYMBOL_MAP = {}
        cls.EMPTY_SYMBOL = Symbol(EMPTY, "", False)
        cls.END_SYMBOL = Symbol(END, "", False)
        cls.END_SYMBOL.isTerminal = True

    @classmethod
    def get(cls, name: str) -> 'Symbol':
        return cls._SYMBOL_MAP[name]

    @classmethod
    def exists(cls, name: str) -> bool:
        return name in cls._SYMBOL_MAP

    @classmethod
    def all(cls) -> Iterable['Symbol']:
        return cls._SYMBOL_MAP.values()

    def __init__(self, name: str, regex: str, nullable: bool) -> None:
        self.id = Symbol._ID_GEN
        self.name = name
        self.regex = regex
        self.isTerminal = len(regex) > 0
        self.nullable = nullable
        self.first: Set['Symbol'] = set()
        self.follow: Set['Symbol'] = set()
        Symbol._ID_GEN += 1
        Symbol._SYMBOL_MAP[self.name] = self

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Symbol):
            return False

        return self.id == value.id

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            raise NotImplementedError()

        return self.name.lower() < other.name.lower()

    def __hash__(self) -> int:
        return self.id


class Rule:

    def __init__(
        self, id: int, nonterm: Symbol, symbols: List[Symbol], code: str, file: str, lineNum: int, codeLine: int
    ) -> None:
        self.id = id
        self.nonterm = nonterm
        self.symbols = symbols
        self.code = code
        # filename that this rule was defined in
        self.file = file
        # line number of the rule in the grammar file
        self.lineNum = lineNum
        # line number of the code block in the grammar file
        self.codeLine = codeLine

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rule):
            return False

        return self.nonterm == other.nonterm and self.symbols == other.symbols

    def __str__(self) -> str:
        return f'Rule {self.id} @line {self.lineNum}: {self.nonterm} = {" ".join([str(x) for x in self.symbols])}'

    def compare(self, other) -> int:
        if not isinstance(other, Rule):
            raise NotImplementedError(f'Cannot compare Rule to {type(other)}')

        if self.nonterm < other.nonterm:
            return -1
        elif self.nonterm > other.nonterm:
            return 1

        if len(self.symbols) < len(other.symbols):
            return -1
        if len(self.symbols) > len(other.symbols):
            return 1

        for x, y in zip(self.symbols, other.symbols):
            x = x.id
            y = y.id
            if x < y:
                return -1
            if x > y:
                return 1

        return 0

    def __lt__(self, other):
        return self.compare(other) == -1

    def __le__(self, other):
        return self.compare(other) <= 0

    def __gt__(self, other):
        return self.compare(other) == 1

    def __ge__(self, other):
        return self.compare(other) >= 0


class _RuleDef:

    def __init__(
        self, id: int, nonterm: str, symbols: List[str], code: str, file: str, lineNum: int, codeLine: int
    ) -> None:
        # these are the same as in Rule

        self.id = id
        self.nonterm = nonterm
        self.symbols = symbols
        self.code = code
        self.file = file
        self.lineNum = lineNum
        self.codeLine = codeLine

    def __str__(self) -> str:
        return f'Rule {self.id} @line {self.lineNum}: {self.nonterm} = {" ".join([str(x) for x in self.symbols])}'


class Grammar:

    def __init__(
        self,
        terminals: List[Tuple[str, str]],
        ruleDefs: List[_RuleDef],
        nulls: Set[str],
        directives: Dict[str, List[str]]
    ) -> None:
        # List of terminals, in order as defined
        self._terminals: List[Symbol] = [Symbol(x[0], x[1], False) for x in terminals]

        # List of each rule
        self.rules: List[Rule] = []
        # construct real rules from definitions
        for rule in ruleDefs:
            try:
                lhs = Symbol.get(rule.nonterm)
            except KeyError:
                lhs = Symbol(rule.nonterm, "", rule.nonterm in nulls)

            rhs = []
            for symbol in rule.symbols:
                # At this point, every terminal has been defined, assume any
                # new symbols are nonterminals (also we error checked this in parse_grammar)
                try:
                    s = Symbol.get(symbol)
                except KeyError:
                    s = Symbol(symbol, "", symbol in nulls)
                rhs.append(s)
            self.rules.append(Rule(rule.id, lhs, rhs, rule.code, rule.file, rule.lineNum, rule.codeLine))

        # Set the start symbol to the first rule
        self.startSymbol = self.rules[0].nonterm

        self.directives = directives

        self._gen_first_and_follow()

    def _gen_first_and_follow(self):
        for symbol in Symbol.all():
            # Initialize the first set to contain nulls
            if symbol.nullable:
                symbol.first.add(Symbol.EMPTY_SYMBOL)
            # Initialize the first set to contain the terminals
            if symbol.isTerminal:
                symbol.first.add(symbol)

        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                curSet = rule.nonterm.first.copy()

                nullable = True
                for symbol in rule.symbols:
                    curSet.update(symbol.first)
                    if not symbol.nullable:
                        nullable = False
                        break

                if nullable:
                    curSet.add(Symbol.EMPTY_SYMBOL)

                if curSet > rule.nonterm.first:
                    rule.nonterm.first = curSet
                    changed = True
            # End for rule
        # End while changed

        self.startSymbol.follow.add(Symbol.END_SYMBOL)

        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                left = rule.nonterm.follow
                # True if the previous symbol had EMPTy in their first set
                lastEmpty = True
                # Iterate backwards to keep track of when the next symbol can be empty
                for i in reversed(range(len(rule.symbols))):
                    curSymbol = rule.symbols[i]
                    if curSymbol == EMPTY:
                        break

                    if lastEmpty:
                        right = curSymbol.follow
                        new = left.union(right)
                        if new > right:
                            curSymbol.follow = new
                            changed = True
                        lastEmpty = Symbol.EMPTY_SYMBOL in curSymbol.first
                    if i > 0:
                        prior = rule.symbols[i - 1]
                        curFirst = curSymbol.first.difference({Symbol.EMPTY_SYMBOL})
                        priorFollow = prior.follow
                        new = priorFollow.union(curFirst)
                        if new > priorFollow:
                            prior.follow = new
                            changed = True
                # End for symbols
            # End for rules
        # End while changed


class _Reader:
    """
    Lets us pass these numbers by reference
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.io = open(filename, mode='r')
        self.lineNum = 1
        self.charNum = 0
        self._lastLineLen = 0
        self._lastChar = ''

    def __del__(self):
        try:
            self.io.close()
        except AttributeError:
            pass

    def __str__(self) -> str:
        return f'{self.filename}:{self.lineNum}:{self.charNum}'

    def get(self) -> str:
        out = self.io.read(1)
        self.charNum += 1

        # python text IO automatically converts CRLF/LR to a single char
        if out == '\n':
            self.lineNum += 1
            self._lastLineLen = self.charNum
            self.charNum = 0

        self._lastChar = out
        return out

    def unget(self):
        # Seek to 1 char before the current position
        # We *should* only ever unget 1 char
        self.io.seek(self.io.tell() - 1, 0)
        if self._lastChar == '\n':
            self.lineNum -= 1
            self.charNum = self._lastLineLen
        else:
            self.charNum -= 1

    def skipComment(self):
        nextChar = self.get()
        if nextChar == '#':
            while True:
                nextChar = self.get()
                if nextChar == '#':
                    nextChar = self.get()
                    if nextChar == '#':
                        break
        else:
            while True:
                if len(nextChar) == 0:
                    break
                if nextChar == '\n':
                    break
                nextChar = self.get()


NAME_CHARS = set('abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
H_ARG_RE = re.compile(r'\$((?P<idx>\d+)|(?P<name>\w+))')


class _GrammarFileParser:

    def __init__(self, rootfile: str) -> None:
        self.terminalNames: Set[str] = set()
        self.terminals: List[Tuple[str, str]] = []
        self.ruleDefs: List[_RuleDef] = []
        self.nonterminals: Set[str] = set()
        self.nulls: Set[str] = set()
        self.directives: Dict[str, List[str]] = defaultdict(list)

        self.rootfile = rootfile
        self.fileQueue = deque([rootfile])

    def parse(self) -> Grammar:
        Symbol.reset()

        while len(self.fileQueue) > 0:
            filename = self.fileQueue.popleft()
            self._parseFile(filename)

        for rule in self.ruleDefs:
            for symbol in rule.symbols:
                if symbol not in self.terminalNames and symbol not in self.nonterminals:
                    raise HermesError(
                        f"{self.rootfile} Missing terminal/nonterminal definitions for symbol: '{symbol}', rule: {rule}"
                    )

            if rule.nonterm in self.terminals:
                raise HermesError(
                    f'{self.rootfile} Symbol defined as both a terminal and nonterminal: "{rule.nonterm}"'
                )

        # TODO check for unused terminals/nonterminals
        # TODO check for bad/unused directives

        if Directive.return_ not in self.directives:
            raise HermesError(f"{self.rootfile} Missing {Directive.return_} directive")
        if len(self.directives[Directive.return_]) > 1:
            raise HermesError(f'{self.rootfile} More than one {Directive.return_} directive provided')

        if Directive.ignore in self.directives:
            processedIgnores = []
            for ignore in self.directives[Directive.ignore]:
                if len(ignore) <= 2:
                    raise HermesError(f"Invalid %ignore, regex cannot be empty")
                if ignore[0] not in "\"'" or ignore[0] != ignore[-1] or ignore[-2] == "\\":
                    raise HermesError(f"Invalid %ignore, regex must be quoted")
                quoteType = ignore[0]
                # Strip quotes
                regex = ignore[1:-1]
                # Replace escaped quotes
                processedIgnores.append(regex.replace(f"\\{quoteType}", quoteType))
            # Replace the ignores list
            self.directives[Directive.ignore] = processedIgnores

        for rule in self.ruleDefs:

            # TODO error message should have different filename if imported
            # TODO error messages should have line numbers

            def preproc(m: re.Match) -> str:
                name = m.group('name')
                if name is not None:
                    try:
                        count = rule.symbols.count(name)
                        if count > 1:
                            raise HermesError(
                                f"{self.rootfile} Cannot substitue symbol '${name}', symbol is repeated in rule, use index instead, {rule}"
                            )
                        elif count == 0:
                            raise HermesError(
                                f"{self.rootfile} Cannot substitute symbol '${name}', symbol not in rule, {rule}"
                            )

                        sIdx = rule.symbols.index(name)
                    except ValueError:
                        raise HermesError(
                            f"{self.rootfile} Invalid code substitution, symbol '{name}' not found, {rule}"
                        ) from None
                else:
                    sIdx = int(m.group('idx'))
                    try:
                        name = rule.symbols[sIdx]
                    except IndexError:
                        raise HermesError(
                            f'{self.rootfile} Invalid code substitution, index {sIdx} out of bounds, {rule}'
                        ) from None

                # Have to invert the index because the stack items will be reversed
                sIdx = len(rule.symbols) - sIdx - 1
                func = "t()" if name in self.terminalNames else "nt()"
                return f'{ARG_VECTOR}[{sIdx}]->{func}'

            # Replace all arg substitutions
            rule.code = H_ARG_RE.sub(preproc, rule.code)

        startSymbol = self.ruleDefs[0].nonterm
        needsNewStart = False
        for r in self.ruleDefs[1:]:
            if r.nonterm == startSymbol:
                needsNewStart = True
                break

        if needsNewStart:
            # we have more than one production for the start symbol
            # condense this into a single production for the start symbol
            # like: __START__ = [start symbol]
            self.ruleDefs = [
                _RuleDef(len(self.ruleDefs), "__START__", [startSymbol, END], "return $0;", "HERMES_GENERATED", 0, 0),
                *self.ruleDefs
            ]

        return Grammar(self.terminals, self.ruleDefs, self.nulls, self.directives)

    def _parseFile(self, filename: str):
        f = _Reader(filename)

        dirname = os.path.split(filename)[0]

        while True:
            nextChar = f.get()
            if len(nextChar) == 0:
                # EOF
                break  # TODO?

            if nextChar in ' \t\n':
                continue

            if nextChar == '%':
                key, val = parse_directive(f)

                if key == Directive.import_:
                    self.fileQueue.append(os.path.join(dirname, val))

                else:
                    self.directives[key].append(val)

                continue

            # Skip comments
            if nextChar == '#':
                f.skipComment()
                continue

            if nextChar not in NAME_CHARS:
                raise HermesError(f"{f} Invalid character '{nextChar}', expected name")

            # Parse LHS of rule
            lhs = nextChar
            while True:
                nextChar = f.get()
                if len(nextChar) == 0:
                    raise HermesError(f"{f} Unexpected EOF")

                if nextChar in ' \t\n':
                    break

                if nextChar not in NAME_CHARS:
                    raise HermesError(f"{f} Invalid character '{nextChar}'")

                lhs += nextChar

            if lhs == _EMPTY_STR:
                raise HermesError(f'{f} LHS cannot be EMPTY')

            # Find equals
            while True:
                nextChar = f.get()
                if len(nextChar) == 0:
                    raise HermesError(f"{f} Unexpected EOF")

                if nextChar == '=':
                    break

                if nextChar == '#':
                    f.skipComment()
                    continue

                if nextChar not in ' \t\n':
                    raise HermesError(f"{f} Invalid character '{nextChar}', expected '='")

            # Find first char
            isTerminal = False
            while True:
                nextChar = f.get()
                if len(nextChar) == 0:
                    raise HermesError(f'{f} Unexpected EOF')

                if nextChar in ' \t\n':
                    continue

                if nextChar in '"\'':
                    isTerminal = True
                    break

                if nextChar in NAME_CHARS:
                    # Else it is a nonTerminal, unget the last char
                    f.unget()
                    break

                if nextChar == '#':
                    f.skipComment()
                    continue

                raise HermesError(f"{f} Invalid character '{nextChar}', expected terminal or symbol list")

            if isTerminal:
                if lhs in self.terminalNames:
                    raise HermesError(f"{f} Duplicate terminal definition '{lhs}'")
                regex = parse_terminal(f, nextChar)
                self.terminalNames.add(lhs)
                self.terminals.append((lhs, regex))
                continue

            self.nonterminals.add(lhs)
            if parse_rules(f, lhs, self.ruleDefs):
                self.nulls.add(lhs)


def parse_directive(f: _Reader) -> Tuple[str, str]:
    key = ''
    value = ''
    hitNewline = False
    while True:
        nextChar = f.get()
        if len(nextChar) == 0:
            raise HermesError(f'{f} Invalid directive, unexpected EOF')

        if len(key) == 0:
            if nextChar not in NAME_CHARS:
                raise HermesError(f"{f} Invalid directive, expected directive name")
            key += nextChar
            continue

        if nextChar in " \t":
            break

        if nextChar == '\n':
            hitNewline = True
            break

        if nextChar not in NAME_CHARS:
            raise HermesError(f"{f} Invalid character '{nextChar}' in directive name")

        key += nextChar

    # Short circuit for empty value
    if hitNewline:
        return key, value

    bracketed = False

    # Read the value
    while True:
        nextChar = f.get()
        if nextChar == '':
            if not bracketed:
                break
            else:
                raise HermesError(f"{f} Unclosed %% in directive")

        if len(value) == 0:
            # Skip leading whitespace
            if nextChar in {" ", "\t"}:
                continue
            if nextChar == '%':
                nextChar = f.get()
                if nextChar == '%':
                    bracketed = True
                else:
                    value += '%'
                    f.unget()
                    continue

        if bracketed and nextChar == '%':
            nextChar = f.get()
            if nextChar == '%':
                break
            else:
                value += '%'
                f.unget()
                continue
        elif bracketed or nextChar != "\n":
            value += nextChar
        else:
            break

    return key, value.strip()


def parse_terminal(f: _Reader, quoteType: str) -> str:
    out = []

    while True:
        nextChar = f.get()
        if len(nextChar) == 0:
            raise HermesError(f'{f} Unexpected EOF')

        if nextChar == quoteType:
            if len(out) == 0:
                raise HermesError(f"{f} Empty terminal regex")
            # check for escaped quote
            if out[-1] != '\\':
                break
            # Else it is escaped, replace the backslash with the quote
            out[-1] = nextChar
            continue

        out.append(nextChar)

    while True:
        nextChar = f.get()
        if nextChar == ';':
            break
        if nextChar not in ' \t\n':
            raise HermesError(f"{f} Invalid character '{nextChar}', expected ';'")

    return "".join(out)


def parse_rules(f: _Reader, lhs: str, rules: List[_RuleDef]) -> bool:
    """
    Parse and add rules to the list, returns true if one of the rules is EMPTY
    """
    isNull = False
    while True:
        curStrSymbolList: List[str] = []
        curSymbol = ''
        curCode = ''
        startingLine = f.lineNum

        # set to -1 if not code block
        curCodeStart = 0

        while True:
            nextChar = f.get()
            if len(nextChar) == 0:
                raise HermesError(f"{f} Unexpected EOF")

            if nextChar == '{':
                if len(curSymbol) > 0:
                    curStrSymbolList.append(curSymbol)
                    curSymbol = ''
                break

            if nextChar in NAME_CHARS:
                curSymbol += nextChar
                continue

            if nextChar in ' \t\n':
                if len(curSymbol) > 0:
                    curStrSymbolList.append(curSymbol)
                    curSymbol = ''
                continue

            if nextChar == '#':
                f.skipComment()
                continue

            if nextChar in '|;':
                curCodeStart = -1
                if len(curSymbol) > 0:
                    curStrSymbolList.append(curSymbol)
                    curSymbol = ''
                break

            raise HermesError(f"{f} Invalid char '{nextChar}' in rule definition, expected symbol or code block")

        # Check for null
        newNull = False
        for symbol in curStrSymbolList:
            if symbol == _EMPTY_STR:
                isNull = True
                newNull = True
                if len(curStrSymbolList) > 1:
                    raise HermesError(f"{f} EMPTY cannot be used in a rule with other symbols")
                break

        # Do this after to not potentially bork the iteration
        if newNull:
            curStrSymbolList = []

        if curCodeStart >= 0:
            while True:
                nextChar = f.get()
                if nextChar not in ' \t\n':
                    f.unget()
                    break

            curCodeStart = f.lineNum

            numOpenBrackets = 1

            while True:
                nextChar = f.get()
                if nextChar == '{':
                    numOpenBrackets += 1
                elif nextChar == '}':
                    numOpenBrackets -= 1
                    if numOpenBrackets == 0:
                        break
                curCode += nextChar
            curCode = curCode.strip()
        else:
            # TODO this is C++ specific
            curCode = "return $0;"
            curCodeStart = f.lineNum
            # unget so the next bit of code can grab the | or ;
            f.unget()

        nextID = len(rules)
        rules.append(_RuleDef(nextID, lhs, curStrSymbolList, curCode, f.filename, startingLine, curCodeStart))

        hitSemi = False
        while True:
            nextChar = f.get()
            if nextChar in ' \t\n':
                continue
            if nextChar == '|':
                break
            if nextChar == ';':
                hitSemi = True
                break
            if nextChar == '#':
                f.skipComment()
                continue

            raise HermesError(f"{f} Invalid char '{nextChar}', expected ';' or '|'")

        if hitSemi:
            break

    return isNull


def parse_grammar(filename: str) -> Grammar:
    parser = _GrammarFileParser(filename)
    return parser.parse()
