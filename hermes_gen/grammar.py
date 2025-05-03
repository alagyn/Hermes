from typing import List, Dict, Set, Tuple, Iterable, Optional, Deque
from collections import deque, defaultdict
import re
import os
import sys

from hermes_gen.errors import HermesError
from hermes_gen.consts import ARG_VECTOR, EMPTY, END, START, ERROR
from hermes_gen.directives import Directive, ALL_DIRECTIVES
from hermes_gen import hermes_logs

DEFAULT_CODE = "return $0;"


class Symbol:
    _ID_GEN = 0
    _SYMBOL_MAP: Dict[str, 'Symbol'] = {}

    EMPTY: 'Symbol' = None  # type: ignore
    END: 'Symbol' = None  # type: ignore
    ERROR: 'Symbol' = None  # type: ignore

    @classmethod
    def reset(cls):
        cls._ID_GEN = 0
        cls._SYMBOL_MAP = {}
        cls.EMPTY = Symbol(EMPTY, "", False)
        cls.END = Symbol(END, "", False)
        cls.ERROR = Symbol(ERROR, "", False)
        cls.ERROR.isTerminal = True
        cls.END.isTerminal = True

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
        if isinstance(value, str):
            return self.name == value
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

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f'Rule {self.id} [{self.nonterm} = {" ".join([str(x) for x in self.symbols])}]'

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
        self, id: int, nonterm: str, symbols: List[str], code: Optional[str], file: str, lineNum: int, codeLine: int
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
        return f'Rule {self.id} {self.file}:{self.lineNum}: {self.nonterm} = {" ".join([str(x) for x in self.symbols])}'


NAME_CHARS = set('abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
H_ARG_RE = re.compile(r'(?P<cmd>\$|@)((?P<idx>\d+)|(?P<name>\w+))')


class Grammar:

    def __init__(self, terminals: List[Symbol], rules: List[Rule], directives: Dict[str, List[str]]) -> None:
        # List of terminals, in order as defined
        self._terminals = terminals
        self._terminalNames: Set[str] = {x.name
                                         for x in terminals}

        # List of each rule
        self.rules = rules

        # Set the start symbol to the first rule
        self.startSymbol = self.rules[0].nonterm

        self.directives = directives

        self._gen_first_and_follow()

    def _gen_first_and_follow(self):
        for symbol in Symbol.all():
            # Initialize the first set to contain nulls
            if symbol.nullable:
                symbol.first.add(Symbol.EMPTY)
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
                    curSet.add(Symbol.EMPTY)

                if curSet > rule.nonterm.first:
                    rule.nonterm.first = curSet
                    changed = True
            # End for rule
        # End while changed

        self.startSymbol.follow.add(Symbol.END)

        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                left = rule.nonterm.follow
                # True if the previous symbol had EMPTY in their first set
                lastEmpty = True
                # Iterate backwards to keep track of when the next symbol can be empty
                for i in reversed(range(len(rule.symbols))):
                    curSymbol = rule.symbols[i]
                    if curSymbol == Symbol.EMPTY:
                        break

                    if lastEmpty:
                        right = curSymbol.follow
                        new = left.union(right)
                        if new > right:
                            curSymbol.follow = new
                            changed = True
                        lastEmpty = Symbol.EMPTY in curSymbol.first
                    if i > 0:
                        prior = rule.symbols[i - 1]
                        curFirst = curSymbol.first.difference({Symbol.EMPTY})
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

    def __init__(self, filename: str, rootdir: Optional[str]) -> None:
        self.filename = filename
        self.printFilename = filename if rootdir is None else os.path.relpath(filename, rootdir)
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
        return f'{self.printFilename}:{self.lineNum}:{self.charNum}'

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


class _TerminalDef:

    def __init__(self, name: str, regex: str, loc: str) -> None:
        self.name = name
        self.regex = regex
        self.loc = loc


class _DirectiveValue:

    def __init__(self, value: str, location: str) -> None:
        self.value = value
        self.location = location


class _GrammarFileParser:

    def __init__(self, rootfile: str) -> None:
        self.terminalNames: Set[str] = set()
        self.terminalDefs: List[_TerminalDef] = []
        self.ruleDefs: List[_RuleDef] = []
        self.nonterminals: Set[str] = set()
        self.nulls: Set[str] = set()
        self.directives: Dict[str, List[_DirectiveValue]] = defaultdict(list)

        self.rootfile = rootfile
        self.rootFileDir = os.path.dirname(rootfile)
        self.fileQueue = deque([rootfile])

        self.error = False

        self.f: _Reader = None  # type: ignore

    def err(self, msg: str, loc: Optional[str] = None):
        if loc is None:
            fullMsg = f'{self.f} {msg}'
        else:
            fullMsg = f'{loc} {msg}'

        hermes_logs.err(fullMsg)
        self.error = True

    def warn(self, msg: str, loc: Optional[str] = None):
        if loc is None:
            fullMsg = f'{self.f} {msg}'
        else:
            fullMsg = f'{loc} {msg}'

        hermes_logs.warn(fullMsg)

    def parse(self) -> Grammar:
        Symbol.reset()

        while len(self.fileQueue) > 0:
            filename = self.fileQueue.popleft()
            self._parseFile(filename)

        try:
            temp = self.directives[Directive.default]
            if len(temp) > 1:
                for x in temp[1:]:
                    self.err(f"Cannot define more than one %default directive", x.location)

            if len(temp) > 0:
                defaultCode = temp[0].value
            else:
                defaultCode = DEFAULT_CODE
        except KeyError:
            defaultCode = DEFAULT_CODE

        try:
            temp = self.directives[Directive.empty]
            if len(temp) > 1:
                for x in temp[1:]:
                    self.err(f"Cannot define more than one %empty directive", x.location)
            if len(temp) > 0:
                defaultEmpty = temp[0].value
            else:
                defaultEmpty = None
        except KeyError:
            defaultEmpty = None

        outRules: List[Rule] = []

        # define every terminal symbol
        outTerminals: List[Symbol] = [Symbol(x.name, x.regex, False) for x in self.terminalDefs]

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
                _RuleDef(len(self.ruleDefs), START, [startSymbol], "return $0;", "HERMES_GENERATED", 0, 0),
                *self.ruleDefs
            ]
            self.warn(
                f"More than one rule using the starting symbol {startSymbol}.\n\t"
                f"Generating starting rule of the form [{START} = {startSymbol}] {{ return $0; }}",
                f'{self.rootfile}'
            )

        usedTerminals: Set[Symbol] = set()

        rulesForSymbol: Dict[Symbol, List[Tuple[Rule, _RuleDef]]] = defaultdict(list)

        for ruleDef in self.ruleDefs:
            # define/get the nonterm symbol
            try:
                lhs = Symbol.get(ruleDef.nonterm)
            except KeyError:
                lhs = Symbol(ruleDef.nonterm, "", ruleDef.nonterm in self.nulls)

            loc = f'{ruleDef.file}:{ruleDef.lineNum}'

            if lhs.isTerminal:
                self.err(f"Cannot have terminal on LHS of rule", loc)
                continue

            rhs: List[Symbol] = []
            for symbol in ruleDef.symbols:
                if symbol not in self.terminalNames and symbol not in self.nonterminals and symbol != ERROR:
                    self.err(f"Missing terminal/nonterminal definitions for symbol: '{symbol}', rule: {ruleDef}", loc)
                else:
                    # At this point, every terminal has been defined, assume any
                    # new symbols are nonterminals
                    try:
                        s = Symbol.get(symbol)
                    except KeyError:
                        s = Symbol(symbol, "", symbol in self.nulls)

                    rhs.append(s)
                    if s.isTerminal:
                        usedTerminals.add(s)

            if ruleDef.code is None:
                if len(ruleDef.symbols) == 0:
                    if defaultEmpty is None:
                        self.err(f"EMPTY action undefined. Add a code block or %empty directive", loc)
                        ruleDef.code = ""
                    else:
                        ruleDef.code = defaultEmpty
                else:
                    ruleDef.code = defaultCode
            # Replace all arg substitutions
            ruleDef.code = H_ARG_RE.sub(lambda m: self._preprocessRule(ruleDef, m), ruleDef.code)

            # construct real rules from definitions
            newRule = Rule(ruleDef.id, lhs, rhs, ruleDef.code, ruleDef.file, ruleDef.lineNum, ruleDef.codeLine)
            outRules.append(newRule)
            rulesForSymbol[lhs].append((newRule, ruleDef))

        # end for rule

        for t in outTerminals:
            if t not in usedTerminals:
                self.warn(f'Unused Terminal: {t} = {t.regex}')

        # find unused nonterminals
        ruleQueue: Deque[Rule] = deque()
        ruleQueue.append(outRules[0])

        usedNonterms: Set[Symbol] = {outRules[0].nonterm}
        # set of symbols that have been seen but maybe not processed yet
        seenNonterms: Set[Symbol] = set()
        while len(ruleQueue) > 0:
            curRule = ruleQueue.popleft()
            usedNonterms.add(curRule.nonterm)
            for symbol in curRule.symbols:
                if not symbol.isTerminal and symbol not in seenNonterms:
                    seenNonterms.add(symbol)
                    for r in rulesForSymbol[symbol]:
                        ruleQueue.append(r[0])

        for nonterm, ruleList in rulesForSymbol.items():
            if nonterm not in usedNonterms:
                for rule, ruleDef in ruleList:
                    self.warn(f"Unreachable rule: {rule}", f'{ruleDef.file}:{ruleDef.lineNum}')

        try:
            returns = self.directives[Directive.return_]
            if len(returns) > 1:
                for x in returns:
                    self.err(f'More than one {Directive.return_} directive provided', x.location)
        except KeyError:
            self.err(f"{self.rootfile} Missing {Directive.return_} directive")

        if Directive.ignore in self.directives:
            for ignore in self.directives[Directive.ignore]:
                regex = ignore.value
                if len(regex) <= 2:
                    self.err(f"Invalid %ignore, regex cannot be empty")
                if regex[0] not in "\"'" or regex[0] != regex[-1] or regex[-2] == "\\":
                    self.err(f"Invalid %ignore, regex must be quoted")
                quoteType = regex[0]
                # Strip quotes
                regex = regex[1:-1]
                # Replace escaped quotes and set the value
                ignore.value = regex.replace(f"\\{quoteType}", quoteType)
        # end if ignore in directives

        outDirectives: Dict[str, List[str]] = {
            d: [v.value for v in vList]
            for d, vList in self.directives.items()
        }

        for d in self.directives:
            if d not in ALL_DIRECTIVES:
                self.warn(f"Unused directive %{d}")

        return Grammar(outTerminals, outRules, outDirectives)

    def _preprocessRule(self, rule: _RuleDef, m: re.Match) -> str:
        """
        Preprocess rule, replacing $ and @ directives
        """
        name = m.group('name')
        if name is not None:
            try:
                count = rule.symbols.count(name)
                if count > 1:
                    raise HermesError(
                        f"{rule.file}:{rule.lineNum} Cannot substitue symbol '${name}', symbol is repeated in rule, use index instead, {rule}"
                    )
                elif count == 0:
                    raise HermesError(
                        f"{rule.file}:{rule.lineNum} Cannot substitute symbol '${name}', symbol not in rule, {rule}"
                    )

                sIdx = rule.symbols.index(name)
            except ValueError:
                raise HermesError(
                    f"{rule.file}:{rule.lineNum} Invalid code substitution, symbol '{name}' not found, {rule}"
                ) from None
        else:
            sIdx = int(m.group('idx'))
            try:
                name = rule.symbols[sIdx]
            except IndexError:
                raise HermesError(
                    f'{rule.file}:{rule.lineNum} Invalid code substitution, index {sIdx} out of bounds, {rule}'
                ) from None

        # Have to invert the index because the stack items will be reversed
        sIdx = len(rule.symbols) - sIdx - 1

        cmd = m.group("cmd")
        if cmd == "$":
            func = "t()" if name in self.terminalNames else "nt()"
        else:
            func = "loc"
        return f'{ARG_VECTOR}[{sIdx}]->{func}'

    def _parseFile(self, filename: str):
        self.f = _Reader(filename, self.rootFileDir)

        dirname = os.path.split(filename)[0]

        while True:
            nextChar = self.f.get()
            if len(nextChar) == 0:
                # EOF
                break

            if nextChar in ' \t\n':
                continue

            if nextChar == '%':
                loc = str(self.f)
                key, val = self.parse_directive()

                if key == Directive.import_:
                    self.fileQueue.append(os.path.join(dirname, val))

                else:
                    self.directives[key].append(_DirectiveValue(val, loc))

                continue

            # Skip comments
            if nextChar == '#':
                self.f.skipComment()
                continue

            if nextChar not in NAME_CHARS:
                self.err(f"Invalid character '{nextChar}', expected name")

            lhsStartloc = str(self.f)

            # Parse LHS of rule
            lhs = nextChar
            while True:
                nextChar = self.f.get()
                if len(nextChar) == 0:
                    self.err(f"Unexpected EOF, expected '='")
                    raise HermesError("Unexpected EOF")

                if nextChar in ' \t\n':
                    break

                if nextChar not in NAME_CHARS:
                    self.err(f"Invalid character '{nextChar}'")

                lhs += nextChar

            if lhs in {EMPTY, START, END, ERROR}:
                self.err(f'LHS cannot be {lhs}')

            # Find equals
            while True:
                nextChar = self.f.get()
                if len(nextChar) == 0:
                    self.err(f"Unexpected EOF, expexted '='")
                    raise HermesError("Unexpected EOF")

                if nextChar == '=':
                    break

                if nextChar == '#':
                    self.f.skipComment()
                    continue

                if nextChar not in ' \t\n':
                    self.err(f"Invalid character '{nextChar}', expected '='")

            # Find first char
            isTerminal = False
            while True:
                nextChar = self.f.get()
                if len(nextChar) == 0:
                    self.err(f'Unexpected EOF, expected terminal or symbol list')
                    raise HermesError("Unexpected EOF")

                if nextChar in ' \t\n':
                    continue

                if nextChar in '"\'':
                    isTerminal = True
                    break

                if nextChar == '#':
                    self.f.skipComment()
                    continue

                # Else it is a nonTerminal, unget the last char
                self.f.unget()
                break

            if isTerminal:
                if lhs in self.terminalNames:
                    self.err(f"Duplicate terminal definition '{lhs}'")
                regex = self.parse_terminal(nextChar)
                self.terminalNames.add(lhs)
                self.terminalDefs.append(_TerminalDef(lhs, regex, lhsStartloc))
                continue

            self.nonterminals.add(lhs)
            if self.parse_rules(lhs):
                self.nulls.add(lhs)

    def parse_directive(self) -> Tuple[str, str]:
        key = ''
        value = ''
        hitNewline = False
        while True:
            nextChar = self.f.get()
            if len(nextChar) == 0:
                self.err(f'Invalid directive, unexpected EOF')
                raise HermesError("Unexpected EOF")

            if len(key) == 0:
                if nextChar not in NAME_CHARS:
                    self.err(f"Invalid directive, expected directive name")
                key += nextChar
                continue

            if nextChar in " \t":
                break

            if nextChar == '\n':
                hitNewline = True
                break

            if nextChar not in NAME_CHARS:
                self.err(f"Invalid character '{nextChar}' in directive name")

            key += nextChar

        # Short circuit for empty value
        if hitNewline:
            return key, value

        bracketed = False

        # Read the value
        while True:
            nextChar = self.f.get()
            if nextChar == '':
                if not bracketed:
                    break
                else:
                    self.err(f"Unexpected EOF, Unclosed %% in directive")
                    raise HermesError("Unexpected EOF")

            if len(value) == 0:
                # Skip leading whitespace
                if nextChar in {" ", "\t"}:
                    continue
                if nextChar == '%':
                    nextChar = self.f.get()
                    if nextChar == '%':
                        bracketed = True
                        # skip opening %
                        nextChar = self.f.get()
                    else:
                        value += '%'
                        self.f.unget()
                        continue

            if bracketed and nextChar == '%':
                nextChar = self.f.get()
                if nextChar == '%':
                    break
                else:
                    value += '%'
                    self.f.unget()
                    continue
            elif bracketed or nextChar != "\n":
                value += nextChar
            else:
                break

        return key, value.strip()

    def parse_terminal(self, quoteType: str) -> str:
        out = []

        while True:
            nextChar = self.f.get()
            if len(nextChar) == 0:
                self.err(f'Unexpected EOF, expected closing quote')
                raise HermesError("Unexpected EOF")

            if nextChar == quoteType:
                if len(out) == 0:
                    self.err(f"Empty terminal regex")
                # check for escaped quote
                if out[-1] != '\\':
                    break
                # Else it is escaped, replace the backslash with the quote
                out[-1] = nextChar
                continue

            out.append(nextChar)

        while True:
            nextChar = self.f.get()
            if nextChar == ';':
                break
            if nextChar not in ' \t\n':
                self.err(f"Invalid character '{nextChar}', expected ';'")
                self.f.unget()
                break

        return "".join(out)

    def parse_rules(self, lhs: str) -> bool:
        """
        Parse and add rules to the list, returns true if one of the rules is EMPTY
        """
        isNull = False
        while True:
            curStrSymbolList: List[str] = []
            curSymbol = ''
            curCode = ''
            startingLine = self.f.lineNum

            # set to -1 if not code block
            curCodeStart = 0

            while True:
                nextChar = self.f.get()
                if len(nextChar) == 0:
                    self.err("Unexpected EOF, expected symbol, code block, |, or ;")
                    raise HermesError(f"Unexpected EOF")

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
                    self.f.skipComment()
                    continue

                if nextChar in '|;':
                    curCodeStart = -1
                    if len(curSymbol) > 0:
                        curStrSymbolList.append(curSymbol)
                        curSymbol = ''
                    break

                self.err(f"Invalid char '{nextChar}' in rule definition, expected symbol or code block")
                return False

            if len(curStrSymbolList) == 0:
                self.warn("Empty rule, prefer using EMPTY to specify such rules")

            # Check for null
            newNull = False
            for symbol in curStrSymbolList:
                if symbol == EMPTY:
                    isNull = True
                    newNull = True
                    if len(curStrSymbolList) > 1:
                        self.err(f"EMPTY cannot be used in a rule with other symbols")
                    break

            # Do this after to not potentially bork the iteration
            if newNull:
                curStrSymbolList = []

            if curCodeStart >= 0:
                # save the leading indentation before the first bit of code
                # so we can remove it from every line
                indentStr = ""
                while True:
                    nextChar = self.f.get()
                    # reset if newline
                    if nextChar == "\n":
                        indentStr = ""
                    elif nextChar in " \t":
                        indentStr += nextChar
                    else:
                        self.f.unget()
                        break

                curCodeStart = self.f.lineNum

                numOpenBrackets = 1

                while True:
                    nextChar = self.f.get()
                    if nextChar == '{':
                        numOpenBrackets += 1
                    elif nextChar == '}':
                        numOpenBrackets -= 1
                        if numOpenBrackets == 0:
                            break
                    curCode += nextChar
                # strip leading indentation
                codeLines = curCode.strip().splitlines()
                for i in range(1, len(codeLines)):
                    codeLine = codeLines[i]
                    if codeLine.startswith(indentStr):
                        codeLines[i] = codeLine[len(indentStr):]
                    else:
                        self.warn(
                            "Inconsistent indentation, may break some language outputs",
                            f'{self.f.filename}:{curCodeStart}'
                        )

                curCode = "\n".join(codeLines)
            else:
                curCode = None
                curCodeStart = startingLine
                # unget so the next bit of code can grab the | or ;
                self.f.unget()

            nextID = len(self.ruleDefs)
            self.ruleDefs.append(
                _RuleDef(nextID, lhs, curStrSymbolList, curCode, self.f.filename, startingLine, curCodeStart)
            )

            hitSemi = False
            while True:
                nextChar = self.f.get()
                if nextChar in ' \t\n':
                    continue
                if nextChar == '|':
                    break
                if nextChar == ';':
                    hitSemi = True
                    break
                if nextChar == '#':
                    self.f.skipComment()
                    continue

                self.err(f"Invalid char '{nextChar}', expected ';' or '|'")
                break

            if hitSemi:
                break

        return isNull


def parse_grammar(filename: str) -> Grammar:
    parser = _GrammarFileParser(filename)
    g = parser.parse()
    if parser.error:
        raise HermesError("Parse Error")
    return g
