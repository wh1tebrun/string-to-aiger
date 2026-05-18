from .regex_ast import Empty, Char, Concat, UnionExpr, Intersect, Star, Regex


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

    def peek(self, offset: int = 1) -> str | None:
        index = self.pos + offset

        if index >= len(self.text):
            return None

        return self.text[index]

    def consume(self, expected: str | None = None) -> str:
        ch = self.current()

        if ch is None:
            raise ValueError("Unexpected end of input")

        if expected is not None and ch != expected:
            raise ValueError(f"Expected '{expected}', got '{ch}' at position {self.pos}")

        self.pos += 1
        return ch

    def consume_escaped_literal(self) -> str:
        self.consume("\\")

        ch = self.current()
        if ch is None:
            raise ValueError("Unexpected end of input after escape character")

        return self.consume()

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

        while self.current() in ("*", "+", "?"):
            operator = self.consume()

            if operator == "*":
                expr = Star(expr)
            elif operator == "+":
                expr = Concat(expr, Star(expr))
            elif operator == "?":
                expr = UnionExpr(Empty(), expr)
            else:
                raise AssertionError(f"Unknown repetition operator: {operator}")

        return expr

    def parse_atom(self) -> Regex:
        ch = self.current()

        if ch is None:
            raise ValueError("Unexpected end of input")

        if ch == "\\":
            return Char(self.consume_escaped_literal())

        if ch == "(":
            self.consume("(")
            expr = self.parse_union()
            self.consume(")")
            return expr

        if ch == "[":
            return self.parse_character_class()

        if ch in "|&)*]+?":
            raise ValueError(f"Unexpected character '{ch}' at position {self.pos}")

        return Char(self.consume())

    def parse_character_class(self) -> Regex:
        self.consume("[")

        options: list[Regex] = []

        while True:
            ch = self.current()

            if ch is None:
                raise ValueError("Unterminated character class")

            if ch == "]":
                self.consume("]")
                break

            start = self.parse_character_class_symbol()

            if start == "[":
                raise ValueError(
                    f"Unexpected '[' inside character class at position {self.pos - 1}"
                )

            if self.current() == "-" and self.peek() not in (None, "]"):
                self.consume("-")
                end = self.parse_character_class_symbol()

                if end in "[]":
                    raise ValueError("Invalid character range in character class")

                options.extend(self.expand_range(start, end))
            else:
                options.append(Char(start))

        if not options:
            raise ValueError("Character class must not be empty")

        return self.union_all(options)

    def parse_character_class_symbol(self) -> str:
        ch = self.current()

        if ch is None:
            raise ValueError("Unterminated character class")

        if ch == "\\":
            return self.consume_escaped_literal()

        return self.consume()

    def expand_range(self, start: str, end: str) -> list[Regex]:
        if ord(start) > ord(end):
            raise ValueError(f"Invalid character range: {start}-{end}")

        return [
            Char(chr(code))
            for code in range(ord(start), ord(end) + 1)
        ]

    def union_all(self, expressions: list[Regex]) -> Regex:
        if not expressions:
            raise ValueError("Expected at least one expression")

        result = expressions[0]

        for expr in expressions[1:]:
            result = UnionExpr(result, expr)

        return result


def parse_regex(text: str) -> Regex:
    """Parse a regular expression into a regex AST."""
    return RegexParser(text).parse()
