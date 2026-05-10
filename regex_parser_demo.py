from regex_parser import parse_regex
from regex_pretty import pretty_regex


examples = [
    "a",
    "ab",
    "a|b",
    "a*",
    "(ab)*",
    "(a|ba)*",
]

for example in examples:
    ast = parse_regex(example)
    print(example, "->", pretty_regex(ast))