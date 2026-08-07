from __future__ import annotations

import csv
import html
import os
import posixpath
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import run_all_tests as test_runner  # noqa: E402


BROKEN_PIPE_FIXTURE = (
    ROOT_DIR / "tests" / "fixtures" / "public_surface" / "broken_pipe_table.md"
)
PUBLIC_MARKDOWN_EXCLUSIONS = ("tests/fixtures/",)
REQUIRED_REPOSITORY_PATHS = (
    ".github/workflows/internal-tests.yml",
    "run_all_tests.py",
)
ALLOWED_TABLE_HTML = frozenset({"br"})


@dataclass(frozen=True, order=True)
class Issue:
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class ProfileCounts:
    full_scripts: int
    full_tests: int
    internal_scripts: int
    internal_tests: int


@dataclass(frozen=True)
class CountClaim:
    path: str
    pattern: re.Pattern[str]
    description: str


COUNT_CLAIMS = (
    CountClaim(
        "README.md",
        re.compile(
            r"The current manifest contains (?P<full_scripts>\d+) scripts and "
            r"(?P<full_tests>\d+) explicit `test_\*` functions\. The internal "
            r"profile runs (?P<internal_scripts>\d+) scripts and "
            r"(?P<internal_tests>\d+) functions;"
        ),
        "README current test-manifest summary",
    ),
    CountClaim(
        "README.md",
        re.compile(
            r"The current \[manifest\]\(run_all_tests\.py\) contains "
            r"(?P<internal_tests>\d+) internal-profile functions in "
            r"(?P<internal_scripts>\d+) scripts;"
        ),
        "README current evidence-map summary",
    ),
    CountClaim(
        "docs/validation_demo.md",
        re.compile(
            r"The current full profile reports (?P<full_scripts>\d+) scripts and "
            r"(?P<full_tests>\d+) explicit test functions\. The internal profile "
            r"reports (?P<internal_scripts>\d+) scripts and "
            r"(?P<internal_tests>\d+) functions;"
        ),
        "validation guide current test summary",
    ),
)


FENCE_START = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*$")
HTML_TAG = re.compile(r"<\s*/?\s*([A-Za-z][A-Za-z0-9-]*)\b[^>]*>")
AUTOLINK = re.compile(
    r"<(?:[A-Za-z][A-Za-z0-9+.-]*:[^ <>]*|[^ <>@]+@[^ <>@]+)>"
)
CORRUPT_BACKTICKS = re.compile(
    r"(?:(?<=[A-Za-z0-9_./\\:-])`{3,}|`{3,}(?=[A-Za-z0-9_./\\:-]))"
)
URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ALIGNMENT_CELL = re.compile(r"^:?-{3,}:?$")
REFERENCE_DEFINITION = re.compile(
    r"^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))(?:\s+.*)?$"
)
REFERENCE_USE = re.compile(r"(!?)\[([^\]]*)\]\[([^\]]*)\]")
SHORTCUT_REFERENCE = re.compile(r"(!?)\[([^\]]+)\]")


def git_tracked_paths(repository_root: Path = ROOT_DIR) -> frozenset[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository_root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise AssertionError(
            f"git ls-files failed with exit {result.returncode}: {stderr}"
        )

    try:
        output = result.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssertionError("git ls-files output is not valid UTF-8") from error

    return frozenset(path for path in output.split("\0") if path)


def public_markdown_paths(tracked_paths: frozenset[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for path in tracked_paths
            if path.endswith(".md")
            and not path.startswith(PUBLIC_MARKDOWN_EXCLUSIONS)
        )
    )


def public_csv_paths(tracked_paths: frozenset[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for path in tracked_paths
            if path.endswith(".csv")
            and (
                path.startswith("artifacts/")
                or path.startswith("evaluation/")
            )
        )
    )


def is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    position = index - 1
    while position >= 0 and text[position] == "\\":
        backslashes += 1
        position -= 1
    return backslashes % 2 == 1


def contains_unescaped_pipe(text: str) -> bool:
    return any(
        character == "|" and not is_escaped(text, index)
        for index, character in enumerate(text)
    )


def split_table_row(line: str) -> list[str]:
    cells: list[str] = []
    start = 0
    for index, character in enumerate(line):
        if character == "|" and not is_escaped(line, index):
            cells.append(line[start:index])
            start = index + 1
    cells.append(line[start:])

    if line.lstrip().startswith("|") and cells and not cells[0].strip():
        cells.pop(0)
    stripped = line.rstrip()
    if stripped.endswith("|") and not is_escaped(stripped, len(stripped) - 1):
        if cells and not cells[-1].strip():
            cells.pop()
    return [cell.strip() for cell in cells]


def inline_code_spans(line: str) -> tuple[tuple[int, int, str], ...]:
    spans: list[tuple[int, int, str]] = []
    index = 0
    while index < len(line):
        if line[index] != "`":
            index += 1
            continue

        end_of_run = index
        while end_of_run < len(line) and line[end_of_run] == "`":
            end_of_run += 1
        delimiter = line[index:end_of_run]
        closing = line.find(delimiter, end_of_run)
        if closing == -1:
            index = end_of_run
            continue

        spans.append((index, closing + len(delimiter), line[end_of_run:closing]))
        index = closing + len(delimiter)
    return tuple(spans)


def mask_inline_code(line: str) -> str:
    masked = list(line)
    for start, end, _content in inline_code_spans(line):
        masked[start:end] = " " * (end - start)
    return "".join(masked)


def fence_mask_and_issues(path: str, lines: list[str]) -> tuple[set[int], list[Issue]]:
    masked_lines: set[int] = set()
    issues: list[Issue] = []
    fence_character: str | None = None
    fence_length = 0
    opener_line = 0

    for line_number, line in enumerate(lines, start=1):
        if fence_character is not None:
            masked_lines.add(line_number)
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}\s*$",
                line,
            )
            if closing:
                fence_character = None
                fence_length = 0
                opener_line = 0
            continue

        opening = FENCE_START.match(line)
        if opening:
            delimiter = opening.group(1)
            fence_character = delimiter[0]
            fence_length = len(delimiter)
            opener_line = line_number
            masked_lines.add(line_number)

    if fence_character is not None:
        issues.append(Issue(path, opener_line, "unbalanced fenced-code block"))

    return masked_lines, issues


def is_alignment_row(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(ALIGNMENT_CELL.fullmatch(cell) for cell in cells)


def is_indented_code_line(line: str) -> bool:
    return line.startswith("    ") or line.startswith("\t")


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return (
        bool(stripped)
        and not is_indented_code_line(line)
        and contains_unescaped_pipe(stripped)
    )


def check_table_cell_syntax(path: str, line_number: int, line: str) -> list[Issue]:
    issues: list[Issue] = []
    for _start, _end, content in inline_code_spans(line):
        if contains_unescaped_pipe(content):
            issues.append(
                Issue(
                    path,
                    line_number,
                    "unescaped '|' inside inline code in a Markdown table row",
                )
            )

    masked = mask_inline_code(line)
    for match in HTML_TAG.finditer(masked):
        tag_name = match.group(1).lower()
        token = match.group(0)
        if AUTOLINK.fullmatch(token):
            continue
        is_plain_break = re.fullmatch(r"<\s*br\s*/?\s*>", token, re.IGNORECASE)
        if tag_name in ALLOWED_TABLE_HTML and is_plain_break:
            continue
        issues.append(
            Issue(
                path,
                line_number,
                f"raw angle-bracket pseudo-tag in table cell: {token}",
            )
        )
    return issues


def check_markdown_tables(
    path: str,
    lines: list[str],
    fenced_lines: set[int],
) -> list[Issue]:
    issues: list[Issue] = []
    index = 0
    while index + 1 < len(lines):
        header_number = index + 1
        alignment_number = index + 2
        if (
            header_number in fenced_lines
            or alignment_number in fenced_lines
            or not is_table_row(lines[index])
            or not is_alignment_row(lines[index + 1])
        ):
            index += 1
            continue

        header_cells = split_table_row(lines[index])
        alignment_cells = split_table_row(lines[index + 1])
        expected_width = len(header_cells)
        if len(alignment_cells) != expected_width:
            issues.append(
                Issue(
                    path,
                    alignment_number,
                    "Markdown table alignment width "
                    f"{len(alignment_cells)} does not match header width {expected_width}",
                )
            )

        issues.extend(check_table_cell_syntax(path, header_number, lines[index]))
        row_index = index + 2
        while row_index < len(lines):
            row_number = row_index + 1
            if row_number in fenced_lines or not is_table_row(lines[row_index]):
                break
            cells = split_table_row(lines[row_index])
            if len(cells) != expected_width:
                issues.append(
                    Issue(
                        path,
                        row_number,
                        "Markdown table row width "
                        f"{len(cells)} does not match header width {expected_width}",
                    )
                )
            issues.extend(check_table_cell_syntax(path, row_number, lines[row_index]))
            row_index += 1
        index = row_index
    return issues


def extract_inline_links(line: str) -> tuple[tuple[str, bool], ...]:
    masked = mask_inline_code(line)
    links: list[tuple[str, bool]] = []
    pattern = re.compile(r"(!?)\[[^\]]*\]\(")
    for match in pattern.finditer(masked):
        bracket_index = match.start() + len(match.group(1))
        if is_escaped(masked, bracket_index):
            continue
        index = match.end()
        depth = 1
        escaped = False
        while index < len(masked) and depth:
            character = masked[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
            index += 1
        if depth:
            continue

        content = line[match.end():index - 1].strip()
        if content.startswith("<") and ">" in content:
            target = content[1:content.index(">")]
        else:
            target = content.split(maxsplit=1)[0] if content else ""
        links.append((target, bool(match.group(1))))
    return tuple(links)


def normalize_reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def reference_definitions(
    lines: list[str],
    fenced_lines: set[int],
) -> dict[str, tuple[str, int]]:
    definitions: dict[str, tuple[str, int]] = {}
    for line_number, line in enumerate(lines, start=1):
        if line_number in fenced_lines or is_indented_code_line(line):
            continue
        match = REFERENCE_DEFINITION.match(mask_inline_code(line))
        if not match:
            continue
        label = normalize_reference_label(match.group(1))
        target = match.group(2) if match.group(2) is not None else match.group(3)
        definitions.setdefault(label, (target, line_number))
    return definitions


def extract_reference_links(line: str) -> tuple[tuple[str, bool], ...]:
    masked = mask_inline_code(line)
    references: list[tuple[str, bool]] = []
    for match in REFERENCE_USE.finditer(masked):
        bracket_index = match.start() + len(match.group(1))
        if is_escaped(masked, bracket_index):
            continue
        label = match.group(3) or match.group(2)
        references.append((normalize_reference_label(label), bool(match.group(1))))
    return tuple(references)


def extract_shortcut_reference_links(
    line: str,
    known_labels: frozenset[str],
) -> tuple[tuple[str, bool], ...]:
    """Return defined GFM shortcut references without treating citations as links."""
    masked = mask_inline_code(line)
    references: list[tuple[str, bool]] = []
    for match in SHORTCUT_REFERENCE.finditer(masked):
        bracket_index = match.start() + len(match.group(1))
        if is_escaped(masked, bracket_index):
            continue
        previous = masked[match.start() - 1] if match.start() else ""
        following = masked[match.end()] if match.end() < len(masked) else ""
        if previous == "]" or following in {"[", "(", ":"}:
            continue
        label = normalize_reference_label(match.group(2))
        if label in known_labels:
            references.append((label, bool(match.group(1))))
    return tuple(references)


def normalize_repository_target(source_path: str, target_path: str) -> str | None:
    decoded = unquote(html.unescape(target_path)).replace("\\", "/")
    if decoded.startswith("/"):
        return None
    source_parent = PurePosixPath(source_path).parent.as_posix()
    combined = posixpath.normpath(posixpath.join(source_parent, decoded))
    if combined == ".":
        return ""
    if combined == ".." or combined.startswith("../"):
        return None
    return PurePosixPath(combined).as_posix()


def exact_tracked_target_exists(target: str, tracked_paths: frozenset[str]) -> bool:
    if target in tracked_paths:
        return True
    prefix = target.rstrip("/") + "/"
    return bool(target) and any(path.startswith(prefix) for path in tracked_paths)


def github_slug(text: str) -> str:
    """Approximate GitHub ATX-heading slugs for the repository's current style."""
    text = re.sub(r"!?(?:\[([^\]]*)\])\([^)]*\)", r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).strip().lower()
    characters = [
        character
        for character in text
        if character.isalnum() or character in {" ", "-", "_"}
    ]
    return re.sub(r"\s+", "-", "".join(characters)).strip("-")


def markdown_anchors(text: str) -> frozenset[str]:
    lines = text.splitlines()
    fenced_lines, _issues = fence_mask_and_issues("<anchor-source>", lines)
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if line_number in fenced_lines:
            continue
        match = HEADING.match(line)
        if not match:
            continue
        heading_text = re.sub(r"\s+#+\s*$", "", match.group(1))
        base = github_slug(heading_text)
        suffix = counts.get(base, 0)
        anchor = base if suffix == 0 else f"{base}-{suffix}"
        counts[base] = suffix + 1
        anchors.add(anchor)
    return frozenset(anchors)


def check_markdown_links(
    repository_root: Path,
    path: str,
    lines: list[str],
    fenced_lines: set[int],
    tracked_paths: frozenset[str],
) -> list[Issue]:
    issues: list[Issue] = []
    anchor_cache: dict[str, frozenset[str]] = {}
    definitions = reference_definitions(lines, fenced_lines)

    def check_target(line_number: int, raw_target: str, is_image: bool) -> None:
        target = raw_target.strip()
        if not target or URI_SCHEME.match(target) or target.startswith("//"):
            return

        path_part, separator, fragment = target.partition("#")
        path_part = path_part.split("?", 1)[0]
        normalized = normalize_repository_target(path, path_part)
        kind = "image" if is_image else "link"
        if normalized is None:
            issues.append(
                Issue(path, line_number, f"local {kind} escapes repository: {target}")
            )
            return

        resolved = path if not path_part else normalized
        if path_part and (
            not exact_tracked_target_exists(resolved, tracked_paths)
            or not (repository_root / resolved).exists()
        ):
            issues.append(
                Issue(
                    path,
                    line_number,
                    f"broken or case-mismatched local {kind}: {target}",
                )
            )
            return

        if not separator or not fragment or not resolved.endswith(".md"):
            return
        if resolved not in tracked_paths:
            return

        if resolved not in anchor_cache:
            target_text = (repository_root / resolved).read_text(encoding="utf-8")
            anchor_cache[resolved] = markdown_anchors(target_text)
        expected_fragment = unquote(fragment).removeprefix("user-content-")
        if expected_fragment not in anchor_cache[resolved]:
            issues.append(
                Issue(
                    path,
                    line_number,
                    f"missing local fragment #{fragment} in {resolved}",
                )
            )

    for line_number, line in enumerate(lines, start=1):
        if line_number in fenced_lines or is_indented_code_line(line):
            continue
        for raw_target, is_image in extract_inline_links(line):
            check_target(line_number, raw_target, is_image)
        for label, is_image in extract_reference_links(line):
            definition = definitions.get(label)
            if definition is None:
                issues.append(
                    Issue(
                        path,
                        line_number,
                        f"undefined Markdown reference label: {label}",
                    )
                )
                continue
            target, _definition_line = definition
            check_target(line_number, target, is_image)
        for label, is_image in extract_shortcut_reference_links(
            line, frozenset(definitions)
        ):
            target, _definition_line = definitions[label]
            check_target(line_number, target, is_image)
    return issues


def check_markdown_document(
    repository_root: Path,
    path: str,
    text: str,
    tracked_paths: frozenset[str],
) -> list[Issue]:
    lines = text.splitlines()
    fenced_lines, issues = fence_mask_and_issues(path, lines)
    for line_number, line in enumerate(lines, start=1):
        if line_number in fenced_lines or is_indented_code_line(line):
            continue
        if CORRUPT_BACKTICKS.search(mask_inline_code(line)):
            issues.append(
                Issue(path, line_number, "triple backticks embedded in word or path")
            )
    issues.extend(check_markdown_tables(path, lines, fenced_lines))
    issues.extend(
        check_markdown_links(
            repository_root,
            path,
            lines,
            fenced_lines,
            tracked_paths,
        )
    )
    return sorted(issues)


def csv_path_header(header: str) -> bool:
    normalized = header.strip().lower()
    return normalized == "path" or normalized.endswith(("_file", "_path"))


def check_csv_file(
    repository_root: Path,
    path: str,
    tracked_paths: frozenset[str],
) -> list[Issue]:
    issues: list[Issue] = []
    try:
        with (repository_root / path).open(newline="", encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        return [Issue(path, 1, f"cannot parse CSV: {error}")]

    if not rows:
        return [Issue(path, 1, "CSV is empty")]
    header = rows[0]
    width = len(header)
    path_columns = [index for index, name in enumerate(header) if csv_path_header(name)]
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != width:
            issues.append(
                Issue(
                    path,
                    row_number,
                    f"CSV row width {len(row)} does not match header width {width}",
                )
            )
            continue
        for column in path_columns:
            target = row[column].strip().replace("\\", "/")
            if not target or URI_SCHEME.match(target):
                continue
            normalized = posixpath.normpath(target)
            if (
                normalized == ".."
                or normalized.startswith("../")
                or normalized.startswith("/")
                or not exact_tracked_target_exists(normalized, tracked_paths)
                or not (repository_root / normalized).exists()
            ):
                issues.append(
                    Issue(
                        path,
                        row_number,
                        f"missing or case-mismatched CSV path in {header[column]}: {target}",
                    )
                )
    return issues


def derive_profile_counts(repository_root: Path = ROOT_DIR) -> ProfileCounts:
    manifest = test_runner.validate_manifest(repository_root=repository_root)
    internal = test_runner.select_test_specs(manifest, internal_only=True)
    return ProfileCounts(
        full_scripts=len(manifest),
        full_tests=test_runner.count_explicit_tests(manifest, repository_root),
        internal_scripts=len(internal),
        internal_tests=test_runner.count_explicit_tests(internal, repository_root),
    )


def check_count_claims(
    repository_root: Path,
    counts: ProfileCounts,
) -> list[Issue]:
    issues: list[Issue] = []
    expected = {
        "full_scripts": counts.full_scripts,
        "full_tests": counts.full_tests,
        "internal_scripts": counts.internal_scripts,
        "internal_tests": counts.internal_tests,
    }
    for claim in COUNT_CLAIMS:
        text = (repository_root / claim.path).read_text(encoding="utf-8")
        matches = list(claim.pattern.finditer(text))
        if len(matches) != 1:
            issues.append(
                Issue(
                    claim.path,
                    1,
                    f"{claim.description} must occur exactly once; found {len(matches)}",
                )
            )
            continue
        match = matches[0]
        line = text.count("\n", 0, match.start()) + 1
        for name, value in match.groupdict().items():
            if int(value) != expected[name]:
                issues.append(
                    Issue(
                        claim.path,
                        line,
                        f"stale {name}: documented {value}, source-derived {expected[name]}",
                    )
                )
    return issues


def run_public_surface_checks(repository_root: Path = ROOT_DIR) -> list[Issue]:
    tracked_paths = git_tracked_paths(repository_root)
    issues: list[Issue] = []

    for required_path in REQUIRED_REPOSITORY_PATHS:
        if (
            required_path not in tracked_paths
            or not (repository_root / required_path).is_file()
        ):
            issues.append(Issue(required_path, 1, "required repository path is not tracked"))

    for path in public_markdown_paths(tracked_paths):
        try:
            text = (repository_root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            issues.append(Issue(path, 1, f"cannot read Markdown as UTF-8: {error}"))
            continue
        issues.extend(check_markdown_document(repository_root, path, text, tracked_paths))

    for path in public_csv_paths(tracked_paths):
        issues.extend(check_csv_file(repository_root, path, tracked_paths))

    try:
        counts = derive_profile_counts(repository_root)
    except (AssertionError, OSError, test_runner.ManifestError) as error:
        issues.append(Issue("run_all_tests.py", 1, f"cannot derive test totals: {error}"))
    else:
        issues.extend(check_count_claims(repository_root, counts))
    return sorted(set(issues))


def format_issues(issues: list[Issue]) -> str:
    return "\n".join(
        f"{issue.path}:{issue.line}: {issue.message}" for issue in sorted(issues)
    )


def fixture_sections() -> tuple[str, str]:
    text = BROKEN_PIPE_FIXTURE.read_text(encoding="utf-8")
    marker = "<!-- corrected companion -->"
    broken, separator, corrected = text.partition(marker)
    assert separator, "broken-pipe fixture is missing its corrected companion marker"
    return broken, corrected


def markdown_fixture_issues(text: str) -> list[Issue]:
    return check_markdown_document(
        ROOT_DIR,
        "fixture.md",
        text,
        frozenset({"fixture.md"}),
    )


def test_broken_pipe_table_fixture_is_rejected() -> None:
    broken, _corrected = fixture_sections()
    issues = markdown_fixture_issues(broken)
    assert any("unescaped '|'" in issue.message for issue in issues), format_issues(issues)
    assert any(issue.line == 7 for issue in issues), format_issues(issues)
    borderless = "pattern | result\n--- | ---\n`a|b` | PASS\n"
    issues = markdown_fixture_issues(borderless)
    assert any("unescaped '|'" in issue.message for issue in issues), format_issues(issues)
    assert any(issue.line == 3 for issue in issues), format_issues(issues)


def test_escaped_pipe_table_is_accepted() -> None:
    _broken, corrected = fixture_sections()
    assert markdown_fixture_issues(corrected) == []
    borderless = "pattern | result\n--- | ---\n`a\\|b` | PASS\n"
    assert markdown_fixture_issues(borderless) == []


def test_normal_table_is_accepted() -> None:
    text = "| name | result |\n| --- | --- |\n| alpha | PASS |\n"
    assert markdown_fixture_issues(text) == []
    borderless = "name | result\n--- | ---\nalpha | PASS\n"
    assert markdown_fixture_issues(borderless) == []
    indented_code = (
        "    pattern | result\n    --- | ---\n    `a|b` | PASS\n"
        "\tpattern | result\n\t--- | ---\n\t`a|b` | PASS\n"
    )
    assert markdown_fixture_issues(indented_code) == []


def test_bad_table_row_width_is_rejected() -> None:
    text = "| name | result |\n| --- | --- |\n| alpha | PASS | extra |\n"
    issues = markdown_fixture_issues(text)
    assert any("row width 3" in issue.message for issue in issues)


def test_raw_pseudo_tag_is_rejected() -> None:
    text = "| trace |\n| --- |\n| <empty> -> end |\n"
    issues = markdown_fixture_issues(text)
    assert any("pseudo-tag" in issue.message for issue in issues)


def test_safe_literal_angle_brackets_are_accepted() -> None:
    text = (
        "| trace |\n| --- |\n"
        "| &lt;empty&gt; -&gt; end |\n"
        "| `<empty> -> end` |\n"
        "| <https://example.com/path> |\n"
        "| <user@example.com> |\n"
    )
    assert markdown_fixture_issues(text) == []


def test_unbalanced_fence_is_rejected() -> None:
    issues = markdown_fixture_issues("```text\ncontent\n")
    assert any("unbalanced" in issue.message for issue in issues)


def test_embedded_corrupt_backticks_are_rejected() -> None:
    issues = markdown_fixture_issues("outputs/file```name.aag\n")
    assert any("triple backticks embedded" in issue.message for issue in issues)
    assert markdown_fixture_issues("Use ```foo``` as literal inline code.\n") == []


def test_valid_fence_is_accepted() -> None:
    text = "```text\n| not | a | table |\n```\n"
    assert markdown_fixture_issues(text) == []


def test_missing_relative_link_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        issues = check_markdown_document(
            root,
            "docs/source.md",
            "[missing](missing.md)\n",
            frozenset({"docs/source.md"}),
        )
    assert any("broken or case-mismatched" in issue.message for issue in issues)
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        reference_text = "[missing][target]\n\n[target]: missing.md\n"
        issues = check_markdown_document(
            root,
            "docs/source.md",
            reference_text,
            frozenset({"docs/source.md"}),
        )
    assert any("broken or case-mismatched" in issue.message for issue in issues)

    undefined = markdown_fixture_issues("[missing][undefined]\n")
    assert any("undefined Markdown reference" in issue.message for issue in undefined)

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        shortcut_text = (
            "[guide]\n![asset]\n\n"
            "[guide]: missing.md\n[asset]: missing.png\n"
        )
        issues = check_markdown_document(
            root,
            "docs/source.md",
            shortcut_text,
            frozenset({"docs/source.md"}),
        )
    assert any("local link" in issue.message for issue in issues)
    assert any("local image" in issue.message for issue in issues)


def test_valid_relative_link_is_accepted() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "docs").mkdir()
        (root / "docs" / "target.md").write_text(
            "# Repeated section\n\n# Repeated section\n",
            encoding="utf-8",
        )
        (root / "docs" / "image.png").write_bytes(b"image")
        tracked = frozenset(
            {"docs/source.md", "docs/target.md", "docs/image.png"}
        )
        issues = check_markdown_document(
            root,
            "docs/source.md",
            "[target](target.md#repeated-section-1)\n"
            "[reference][doc]\n![image][asset]\n"
            "[doc]\n![asset]\n"
            "[doc]: target.md#repeated-section-1\n"
            "[asset]: image.png\n"
            "[external][web]\n[web]: https://example.com/path\n"
            "`[ignored][undefined]`\n",
            tracked,
        )
    assert issues == []

    escaped = markdown_fixture_issues(
        "\\[literal](missing.md)\n\\[literal][undefined]\n"
    )
    assert escaped == []


def test_invalid_csv_width_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        path = "artifacts/example.csv"
        (root / "artifacts").mkdir()
        (root / path).write_text("name,result\nalpha,PASS,extra\n", encoding="utf-8")
        issues = check_csv_file(root, path, frozenset({path}))
    assert any("CSV row width 3" in issue.message for issue in issues)


def test_valid_quoted_csv_is_accepted() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        path = "evaluation/example.csv"
        (root / "evaluation").mkdir()
        (root / path).write_text(
            'name,description\nalpha,"value, with comma"\n',
            encoding="utf-8",
        )
        issues = check_csv_file(root, path, frozenset({path}))
    assert issues == []


def test_current_repository_public_surface_passes() -> None:
    issues = run_public_surface_checks(ROOT_DIR)
    assert issues == [], "Public-surface QA failed:\n" + format_issues(issues)


def run_tests() -> None:
    test_broken_pipe_table_fixture_is_rejected()
    test_escaped_pipe_table_is_accepted()
    test_normal_table_is_accepted()
    test_bad_table_row_width_is_rejected()
    test_raw_pseudo_tag_is_rejected()
    test_safe_literal_angle_brackets_are_accepted()
    test_unbalanced_fence_is_rejected()
    test_embedded_corrupt_backticks_are_rejected()
    test_valid_fence_is_accepted()
    test_missing_relative_link_is_rejected()
    test_valid_relative_link_is_accepted()
    test_invalid_csv_width_is_rejected()
    test_valid_quoted_csv_is_accepted()
    test_current_repository_public_surface_passes()
    print("All public-surface documentation QA tests passed.")


if __name__ == "__main__":
    run_tests()
