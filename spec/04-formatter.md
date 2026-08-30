# 4. Canonical formatter behavior

**Status: stable and normative for language version `0.2.0` for
any implementation that claims to provide `fmt`. Derived from
`crates/scorium-format/src/printer.rs`.**

## Whether formatting is required

Providing a formatter is optional in language version `0.2.0`. An
implementation that exposes `fmt`, `format`, or an equivalent formatter API
MUST follow this entire section and the formatter fixtures.

## Structural rules

- **Indentation**: 4 spaces per nesting level (`FormatOptions.indent_width`
  default). Tabs are never emitted.
- **Node bodies**: `name [header] {\n<indented items>\n}` — the opening
  brace is on the same line as the name/header, the closing brace is on
  its own line at the parent's indent.
- **Blank lines**: at most one consecutive blank line is ever emitted
  between items, and only where the source had at least one blank line at
  that position. This makes formatting idempotent by construction:
  reformatting already-canonical output must reproduce exactly the blank
  lines that are already there, never collapse or multiply them.
- **Trailing whitespace**: the output never ends with more than one
  trailing newline (multiple trailing blank lines collapse to none), and
  always ends with exactly one newline if the output is non-empty.
- **Every item ends its line** with `\n`, including a trailing same-line
  comment (`item <space><comment>\n`), before the next item's leading
  comments/blank-line handling runs.

## Comment rendering

- Line comments render as `# <text>` (space after `#`, source text
  trimmed) — regardless of whether the source used `#` or `--`, canonical
  form is always `#`. `--` line comments MUST normalize to `#` on format.
- Block comments render as `--[[<text>]]` verbatim (not reindented or
  rewrapped internally).
- Comment preservation granularity is item/statement-level only: a leading
  comment (own line, directly above an item) and a trailing comment (same
  line, after an item) are preserved; a comment between `=` and its value,
  or inside a list/call's parentheses, is **not** tracked by the AST and
  is dropped by the formatter. This is a known, documented limitation —
  not a bug to silently work around differently per implementation.

## Expression printing

- Binary operators print with a single space on each side
  (`a + b`, never `a+b`), matching the grammar's own requirement that
  squeezed operators are a lexer error (§1) — the formatter never needs to
  *introduce* squeezing, only preserve the spacing rule.
- **Parenthesization is precedence-driven, not source-preserving**: the
  parser drops explicit grouping parens from the AST, so the formatter
  must re-derive exactly the parens needed to preserve meaning, using this
  precedence table (highest binds tightest):

  ```
  or                                    (lowest)
  and
  == ~= < > <= >=
  + -
  * / %
  unary - / unary not
  call / member (`f(...)`, `.field`)
  literals / parenthesized / lists      (highest)
  ```

  All binary operators are left-associative. When printing a binary
  expression's right operand, the formatter requires strictly higher
  precedence than the operator's own to decide whether to parenthesize —
  this is what correctly re-parenthesizes an explicitly-grouped
  right-associated expression like `a - (b - c)` (which is *not*
  equivalent to `a - b - c`) while never adding redundant parens to a
  left-associated chain like `a - b - c`.

- **Float literals always print with an explicit decimal point**
  (`1.0`, never `1`, for a whole-number float) — printing `1` for a float
  value would silently re-lex as `Int` on the next parse, changing the
  value's type. This rule does not apply to duration amounts: `600` and
  `600.0` both re-lex as the same duration literal, so the formatter emits
  the shorter integer-looking form for a whole-number duration amount.
- String literals: quoted strings re-escape `" \ \n \t \r`; bare strings
  print their literal parts verbatim and re-emit `$name` for each
  interpolation part.
- Lists print as `[a, b, c]` — comma-space separated, no trailing comma.
- Version `0.2.0` performs no automatic line wrapping for any construct,
  regardless of line length.

## Idempotency requirement

Formatting output that is already canonical MUST be a no-op (byte-for-byte
identical). This is the property `fmt --check` relies on and MUST hold for
every formatter fixture's `output` string (see `conformance/README.md`).

## Cross-implementation conformance (resolved: unified, not per-language)

**Decided:** "canonical" means one canonical output, shared by every
implementation — not each implementation's own idea of tidy formatting.
Every rule in this document (indentation, blank-line handling, comment
rendering, the precedence-driven parenthesization table, float/duration
literal formatting, string escaping, list rendering) is a single global
answer, not a per-language style choice. There is deliberately no
"Go-flavored" or "JS-flavored" canonical Scorium — that would defeat the
point of a shared formatter contract, since two implementations' `fmt`
output for the same input would then legitimately disagree and every
consumer would need to know which implementation formatted a given file.

Concretely, for any implementation that provides `fmt`:

- Given the same input and the same `FormatOptions` (currently just
  `indent_width`, default `4`), its output MUST be byte-for-byte identical
  to every other conforming implementation's output — not merely
  idempotent within itself.
- The conformance fixture corpus (`conformance/README.md`) MUST include a
  `formatter/` category of golden `input`/`output` strings that every
  implementation claiming formatter support compares byte-for-byte, not just
  a per-implementation idempotency self-check.
This resolves the earlier open question in the other direction from a
weaker "idempotent per-implementation only" reading: cross-language byte
identity is the goal, and formatter conformance fixtures exist
specifically to catch and prevent per-implementation formatting drift.

## Version scope

Future language versions MAY introduce an explicit wrapping option. Such an
option cannot change the default `0.2.0` output retroactively and requires
versioned conformance fixtures before it becomes normative.
