from typing import List, Dict, Set, Tuple, Optional
import re

from hermes_gen.errors import PTGError


class Rule:

    def __init__(self, id: int, nonterm: str, symbols: List[str], code: str) -> None:
        self.id = id
        self.nonterm = nonterm
        self.symbols = symbols
        self.code = code

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rule):
            return False

        return self.nonterm == other.nonterm and self.symbols == other.symbols

    def __str__(self) -> str:
        return f'Rule: {self.nonterm} = {" ".join(self.symbols)}'

    def compare(self, other) -> int:
        if not isinstance(other, Rule):
            raise NotImplementedError(f'Cannot compare Rule to {type(other)}')

        snt = self.nonterm.lower()
        ont = other.nonterm.lower()

        if snt < ont:
            return -1
        elif snt > ont:
            return 1

        if len(self.symbols) < len(other.symbols):
            return -1
        if len(self.symbols) > len(other.symbols):
            return 1

        for x, y in zip(self.symbols, other.symbols):
            x = x.lower()
            y = y.lower()
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


class Grammer:

    def __init__(
        self,
        terminals: List[Tuple[str, str]],
        rules: List[Rule],
        nulls: Set[str],
        directives: Dict[str, Optional[str]]
    ) -> None:
        # List of each rule
        self.rules = rules
        # Set of nonterminals that can go to null
        self.nulls = nulls
        # Map of name -> regex
        self.terminalList = terminals
        self.terminals = {
            x[0]: x[1]
            for x in self.terminalList
        }

        # The set of every symbol defined in our grammer
        self.symbols = set(self.terminals.keys())
        for rule in self.rules:
            self.symbols.add(rule.nonterm)
            self.symbols.update(rule.symbols)
        # Set the start symbol to the first rule
        self.startSymbol = self.rules[0].nonterm

        self.directives = directives


TERMINAL_RE = re.compile(r'(?P<name>\w+)\s*=\s*(?P<regex>(\'[^\']+\')|("[^"]+"))\s*;')
TOTAL_RULE_RE = re.compile(r'(?P<nonterm>\w+)\s*=(?P<rules>.+);$')
RULE_RE = re.compile(r'(?P<symbols>\w+(\s+\w+)*)(\s*\{(?P<code>[^{}]*)\})?')
DIRECTIVE_RE = re.compile(r'\%(?P<name>\w+)\s+(?P<value>.*)')


def parse_grammer(lines: List[str]) -> Grammer:
    terminalNames = set()
    terminals: List[Tuple[str, str]] = []
    rules: List[Rule] = []
    nonterminals = set()
    nulls = set()
    ruleId = 0
    directives: Dict[str, Optional[str]] = {}

    error = False
    for line in lines:
        m = DIRECTIVE_RE.fullmatch(line)
        if m is not None:
            name = m.group('name')
            value = m.group('value')

            if name in directives:
                print(f"Grammer: Duplicated directive: {name}")
                error = True
                continue

            directives[name] = value
            continue

        m = TERMINAL_RE.fullmatch(line)
        if m is not None:
            name = m.group("name")
            regex = m.group("regex")
            if regex.startswith('"'):
                regex = regex.strip('"')
            else:
                regex = regex.strip("'")
            if name in terminalNames:
                print(f'Grammer: Duplicate terminal definition: "{name}"')
                error = True
                continue

            terminals.append((name, regex))
            terminalNames.add(name)
            continue

        m = TOTAL_RULE_RE.fullmatch(line)
        if m is not None:
            nonterm = m.group("nonterm")
            rule_list_str = m.group("rules")
            for rule in RULE_RE.finditer(rule_list_str):
                symbol_str = rule.group('symbols').strip()
                symbols = []
                for x in symbol_str.split(" "):
                    x = x.strip()
                    if len(x) > 0:
                        symbols.append(x)

                gotNull = False
                for x in symbols:
                    if x == "EMPTY":
                        if len(symbols) > 1:
                            print("EMPTY must be specified in its own rule")
                            error = True
                            continue
                        nulls.add(nonterm)
                        gotNull = True

                if gotNull:
                    symbols = []

                nonterminals.add(nonterm)
                code = rule.group('code')
                if code is None:
                    print("Grammer: Invalid line, missing action block:", line)
                    error = True
                    continue
                else:
                    code = code.strip()
                rules.append(Rule(ruleId, nonterm, symbols, code))
                ruleId += 1
            continue

        print("Grammer: Invalid line:", line)
        error = True

    if error:
        raise PTGError("Bad Parse")

    for rule in rules:
        for symbol in rule.symbols:
            if symbol not in terminalNames and symbol not in nonterminals:
                raise PTGError(f"Missing terminal/nonterminal definitions for symbol: {symbol}")

        if rule.nonterm in terminals:
            raise PTGError(f'Symbol defined as both a terminal and nonterminal: "{rule.nonterm}"')

    # TODO warnings for unused symbols

    return Grammer(terminals, rules, nulls, directives)
