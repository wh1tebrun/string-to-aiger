from regex_parser import parse_regex
from regex_pretty import pretty_regex


examples = [
    "a",
    "ab",
    "a|b",
    "a*",
    "(ab)*",
    "(a|ba)*",
    "a*&b*",
    "(a|b)*&a*",
    "(a|ba)*&a*",
]

for example in examples:
    ast = parse_regex(example)
    print(example, "->", pretty_regex(ast))
