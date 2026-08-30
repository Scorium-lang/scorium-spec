#!/usr/bin/env python3
"""Validate the versioned Scorium specification and conformance corpus."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")
STALE_DRAFT_PATTERN = re.compile(r"\b[0-9]+\.[0-9]+\.[0-9]+-draft\b")
LOCAL_LINK_PATTERN = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
ERROR_CODE_PATTERN = re.compile(r"scorium::[a-z_]+::[a-z0-9_]+")
INTEGER_PATTERN = re.compile(r"-?(?:0|[1-9][0-9]*)")
COLOR_PATTERN = re.compile(r"#[0-9A-F]{8}")
DURATION_PATTERN = re.compile(
    r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?(?:ms|s|m)"
)
FIXTURE_CATEGORIES = {
    "diagnostics",
    "evaluation",
    "formatter",
    "grammar",
    "sandbox",
    "values",
}
VALUE_TYPES = {"int", "float", "bool", "nil", "string", "color", "duration", "list"}
RUNTIME_OPTIONS = {
    "max_loop_iterations",
    "max_function_call_depth",
    "max_script_instructions",
    "max_script_memory_bytes",
}

errors: list[str] = []


def error(path: Path, message: str) -> None:
    try:
        shown = path.relative_to(ROOT)
    except ValueError:
        shown = path
    errors.append(f"{shown}: {message}")


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def require_keys(path: Path, value: dict[str, object], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        error(path, f"{context} keys must be {sorted(expected)}, found {sorted(actual)}")


def validate_semantic_value(path: Path, value: object, context: str) -> None:
    if not isinstance(value, dict):
        error(path, f"{context} must be an object")
        return

    value_type = value.get("type")
    if value_type == "entries":
        require_keys(path, value, {"type", "value"}, context)
        entries = value.get("value")
        if not isinstance(entries, list):
            error(path, f"{context}.value must be an array")
            return
        for index, entry in enumerate(entries):
            validate_entry(path, entry, f"{context}.value[{index}]")
        return

    if value_type not in VALUE_TYPES:
        error(path, f"{context}.type is not a recognized semantic tag")
        return

    if value_type == "nil":
        require_keys(path, value, {"type"}, context)
        return

    require_keys(path, value, {"type", "value"}, context)
    encoded = value.get("value")

    if value_type == "int" and (
        not isinstance(encoded, str) or INTEGER_PATTERN.fullmatch(encoded) is None
    ):
        error(path, f"{context}.value must be a canonical decimal integer string")
    elif value_type == "float":
        if not isinstance(encoded, str):
            error(path, f"{context}.value must be a float string")
        elif encoded not in {"nan", "inf", "-inf"}:
            try:
                float(encoded)
            except ValueError:
                error(path, f"{context}.value is not a valid float string")
    elif value_type == "bool" and type(encoded) is not bool:
        error(path, f"{context}.value must be a JSON boolean")
    elif value_type == "string" and not isinstance(encoded, str):
        error(path, f"{context}.value must be a string")
    elif value_type == "color" and (
        not isinstance(encoded, str) or COLOR_PATTERN.fullmatch(encoded) is None
    ):
        error(path, f"{context}.value must have the form #RRGGBBAA")
    elif value_type == "duration" and (
        not isinstance(encoded, str) or DURATION_PATTERN.fullmatch(encoded) is None
    ):
        error(path, f"{context}.value must be an amount followed by ms, s, or m")
    elif value_type == "list":
        if not isinstance(encoded, list):
            error(path, f"{context}.value must be an array")
        else:
            for index, item in enumerate(encoded):
                validate_semantic_value(path, item, f"{context}.value[{index}]")


def validate_entry(path: Path, entry: object, context: str) -> None:
    if not isinstance(entry, dict):
        error(path, f"{context} must be an object")
        return

    kind = entry.get("kind")
    if kind == "leaf":
        require_keys(path, entry, {"kind", "key", "value"}, context)
        if not isinstance(entry.get("key"), str):
            error(path, f"{context}.key must be a string")
        validate_semantic_value(path, entry.get("value"), f"{context}.value")
    elif kind == "node":
        require_keys(path, entry, {"kind", "name", "header", "children"}, context)
        if not isinstance(entry.get("name"), str):
            error(path, f"{context}.name must be a string")
        if entry.get("header") is not None and not isinstance(entry.get("header"), str):
            error(path, f"{context}.header must be a string or null")
        children = entry.get("children")
        if not isinstance(children, list):
            error(path, f"{context}.children must be an array")
        else:
            for index, child in enumerate(children):
                validate_entry(path, child, f"{context}.children[{index}]")
    elif kind == "include":
        require_keys(path, entry, {"kind", "path"}, context)
        if not isinstance(entry.get("path"), str):
            error(path, f"{context}.path must be a string")
    else:
        error(path, f"{context}.kind is not leaf, node, or include")


def validate_fixture(path: Path, fixture: object) -> str | None:
    if not isinstance(fixture, dict):
        error(path, "fixture root must be an object")
        return None

    name = fixture.get("name")
    if not isinstance(name, str) or not name.strip():
        error(path, "name must be a non-empty string")
        name = None

    requires = fixture.get("requires")
    if requires is not None and (
        not isinstance(requires, list)
        or not all(isinstance(item, str) and item for item in requires)
        or len(set(requires)) != len(requires)
    ):
        error(path, "requires must be an array of unique, non-empty strings")

    category = path.parent.name
    if category == "formatter":
        allowed = {"name", "input", "output", "requires"}
        unknown = set(fixture) - allowed
        if unknown:
            error(path, f"formatter fixture has unknown keys: {sorted(unknown)}")
        for field in ("input", "output"):
            if not isinstance(fixture.get(field), str):
                error(path, f"{field} must be a string")
        return name

    allowed = {"name", "source", "files", "entry", "expect", "expect_error", "requires", "options"}
    unknown = set(fixture) - allowed
    if unknown:
        error(path, f"fixture has unknown keys: {sorted(unknown)}")

    options = fixture.get("options")
    if options is not None:
        if not isinstance(options, dict):
            error(path, "options must be an object")
        else:
            unknown_options = set(options) - RUNTIME_OPTIONS
            if unknown_options:
                error(path, f"options has unknown keys: {sorted(unknown_options)}")
            for option, value in options.items():
                minimum = 0 if option == "max_script_memory_bytes" else 1
                if type(value) is not int or value < minimum:
                    error(path, f"options.{option} must be an integer >= {minimum}")

    has_source = "source" in fixture
    has_files = "files" in fixture or "entry" in fixture
    if has_source == has_files:
        error(path, "use exactly one of source or files+entry")
    elif has_source and not isinstance(fixture.get("source"), str):
        error(path, "source must be a string")
    elif has_files:
        files = fixture.get("files")
        entry = fixture.get("entry")
        if not isinstance(files, dict) or not files:
            error(path, "files must be a non-empty object")
        elif not all(isinstance(key, str) and isinstance(value, str) for key, value in files.items()):
            error(path, "files must map string paths to string contents")
        if not isinstance(entry, str) or not isinstance(files, dict) or entry not in files:
            error(path, "entry must name a file present in files")

    has_expect = "expect" in fixture
    has_error = "expect_error" in fixture
    if has_expect == has_error:
        error(path, "use exactly one of expect or expect_error")
    elif has_expect:
        validate_semantic_value(path, fixture.get("expect"), "expect")
    else:
        expected_error = fixture.get("expect_error")
        if not isinstance(expected_error, dict):
            error(path, "expect_error must be an object")
        elif not isinstance(expected_error.get("code"), str) or ERROR_CODE_PATTERN.fullmatch(
            expected_error["code"]
        ) is None:
            error(path, "expect_error.code must be a Scorium diagnostic code")

    return name


def validate_markdown_links() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        for match in LOCAL_LINK_PATTERN.finditer(path.read_text(encoding="utf-8")):
            target = match.group(1).strip()
            if " " in target:
                target = target.split(" ", 1)[0]
            target = target.strip("<>")
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            relative_target = unquote(target.split("#", 1)[0])
            if relative_target and not (path.parent / relative_target).resolve().exists():
                error(path, f"local link target does not exist: {target}")


def main() -> int:
    version_file = ROOT / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip()
    if VERSION_PATTERN.fullmatch(version) is None:
        error(version_file, "must contain one valid SemVer-like language version")

    version_dir = ROOT / "conformance" / f"v{version}"
    if not version_dir.is_dir():
        error(version_file, f"matching fixture directory is missing: conformance/v{version}")

    current_docs = [ROOT / "README.md", ROOT / "conformance" / "README.md"]
    current_docs.extend(sorted((ROOT / "spec").glob("*.md")))
    for path in current_docs:
        for reference in STALE_DRAFT_PATTERN.findall(path.read_text(encoding="utf-8")):
            if reference != version:
                error(path, f"stale language-version reference {reference!r}; current is {version!r}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if re.search(rf"^## \[?{re.escape(version)}\]?(?:\s|$)", changelog, re.MULTILINE) is None:
        error(ROOT / "CHANGELOG.md", f"missing section for {version}")

    fixtures = sorted(version_dir.glob("*/*.json")) if version_dir.is_dir() else []
    if not fixtures:
        error(version_dir, "current language version has no JSON fixtures")

    names: dict[str, Path] = {}
    for path in fixtures:
        if path.parent.name not in FIXTURE_CATEGORIES:
            error(path, f"unknown fixture category {path.parent.name!r}")
        try:
            fixture = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            error(path, f"invalid JSON: {exc}")
            continue
        name = validate_fixture(path, fixture)
        if name is not None:
            if name in names:
                error(path, f"fixture name duplicates {names[name].relative_to(ROOT)}")
            else:
                names[name] = path

    validate_markdown_links()

    if errors:
        for message in errors:
            print(f"error: {message}", file=sys.stderr)
        print(f"validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(f"validated language {version}: {len(fixtures)} fixtures and {len(current_docs)} spec documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
