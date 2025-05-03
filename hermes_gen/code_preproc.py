import re

from hermes_gen.grammar import Grammar, Rule
from hermes_gen.errors import HermesError

H_ARG_RE = re.compile(r'(?P<cmd>\$|@)((?P<idx>\d+)|(?P<name>\w+))')


class CodePreprocessor:

    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar

    def preproc(self, rule: Rule) -> str:
        """
        Preprocess rule, replacing $ and @ directives
        """
        return H_ARG_RE.sub(lambda m: self._preprocSub(rule, m), rule.code)

    def _preprocSub(self, rule: Rule, m: re.Match) -> str:
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
                name = rule.symbols[sIdx].name
            except IndexError:
                raise HermesError(
                    f'{rule.file}:{rule.lineNum} Invalid code substitution, index {sIdx} out of bounds, {rule}'
                ) from None

        # Have to invert the index because the stack items will be reversed
        sIdx = len(rule.symbols) - sIdx - 1

        cmd = m.group("cmd")
        if cmd == "$":
            if name in self.grammar._terminalNames:
                return self._getTerminal(sIdx)
            else:
                return self._getNonterminal(sIdx)
        else:
            return self._getLoc(sIdx)

    def _getTerminal(self, sIdx: int) -> str:
        raise NotImplementedError()

    def _getNonterminal(self, sIdx: int) -> str:
        raise NotImplementedError()

    def _getLoc(self, sIdx: int) -> str:
        raise NotImplementedError()
