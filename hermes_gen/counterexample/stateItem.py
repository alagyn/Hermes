from hermes_gen.lalr1_automata import Node, AnnotRule


class StateItem:

    def __init__(self, node: Node, rule: AnnotRule) -> None:
        self.node = node
        self.rule = rule

    def __str__(self) -> str:
        return f'{str(self.node)} {str(self.rule)}'

    def __repr__(self) -> str:
        return self.__str__()
