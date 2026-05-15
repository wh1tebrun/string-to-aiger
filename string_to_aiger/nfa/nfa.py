from dataclasses import dataclass, field


State = int
Symbol = str | None
# None means epsilon transition.


@dataclass
class NFA:
    start: State
    accepts: set[State]
    transitions: dict[State, list[tuple[Symbol, State]]] = field(default_factory=dict)

    def add_transition(self, source: State, symbol: Symbol, target: State) -> None:
        if source not in self.transitions:
            self.transitions[source] = []

        self.transitions[source].append((symbol, target))

    def states(self) -> set[State]:
        result = {self.start} | set(self.accepts)

        for source, edges in self.transitions.items():
            result.add(source)
            for _symbol, target in edges:
                result.add(target)

        return result