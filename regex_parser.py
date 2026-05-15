from regex_ast import Char, Concat, UnionExpr, Intersect, Star, Regex


class RegexParser:
    def __init__(self, text: str):
        self.text = text.replace(" ", "")
        self.pos = 0

    def parse(self) -> Regex:
        if not self.text:
            raise ValueError("Regex must not be empty")

        expr = self.parse_union()

        if self.pos != len(self.text):
            raise ValueError(
                f"Unexpected character at position {self.pos}: {self.text[self.pos]}"
            )

        return expr

    def current(self) -> str | None:
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def consume(self, expected: str | None = None) -> str:
        ch = self.current()

        if ch is None:
            raise ValueError("Unexpected end of input")

        if expected is not None and ch != expected:
            raise ValueError(f"Expected '{expected}', got '{ch}' at position {self.pos}")

        self.pos += 1
        return ch

    def parse_union(self) -> Regex:
        left = self.parse_intersection()

        while self.current() == "|":
            self.consume("|")
            right = self.parse_intersection()
            left = UnionExpr(left, right)

        return left

    def parse_intersection(self) -> Regex:
        left = self.parse_concat()

        while self.current() == "&":
            self.consume("&")
            right = self.parse_concat()
            left = Intersect(left, right)

        return left

    def parse_concat(self) -> Regex:
        parts: list[Regex] = []

        while True:
            ch = self.current()

            if ch is None or ch in "|&)":
                break

            parts.append(self.parse_repeat())

        if not parts:
            raise ValueError(f"Expected expression at position {self.pos}")

        result = parts[0]
        for part in parts[1:]:
            result = Concat(result, part)

        return result

    def parse_repeat(self) -> Regex:
        expr = self.parse_atom()

        while self.current() == "*":
            self.consume("*")
            expr = Star(expr)

        return expr

    def parse_atom(self) -> Regex:
        ch = self.current()

        if ch is None:
            raise ValueError("Unexpected end of input")

        if ch == "(":
            self.consume("(")
            expr = self.parse_union()
            self.consume(")")
            return expr

        if ch in "|&)*":
            raise ValueError(f"Unexpected character '{ch}' at position {self.pos}")

        return Char(self.consume())


def parse_regex(text: str) -> Regex:
    """Parse a regular expression into a regex AST."""
    return RegexParser(text).parse()
