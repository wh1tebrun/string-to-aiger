import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from regex_to_aiger import compile_regex_to_aiger  # noqa: E402


def main():
    pattern = "a*"
    bound = 3

    aiger_text = compile_regex_to_aiger(pattern, bound)

    with open("regex_output.aag", "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print("Pattern:", pattern)
    print("Bound:", bound)
    print("Written to regex_output.aag")


if __name__ == "__main__":
    main()
