# Conformance fixtures

**Status: stable schema for language version `0.2.0`. The corpus contains
34 fixtures under `v0.2.0/`, grounded in verified implementation behavior
and the normative decisions recorded by this specification.**

## Intent

Each native implementation runs the same fixture corpus in its own CI,
against whichever spec version it claims to support
(`conformance/v<version>/`). A fixture failure means that implementation is
not conformant at that version -- not a bug report against the spec.

Producing this JSON format is **not** something an implementation needs to
support at all; only conformance-test tooling needs to read it. A fixture
describes an input and an expected outcome -- the encoding below exists so
that description is unambiguous across languages, nothing more.

## One JSON file per fixture

Each fixture is a single self-contained `.json` file at
`conformance/<version>/<category>/<name>.json`. `<category>` matches a
spec section: `values/`, `evaluation/`, `diagnostics/`, `formatter/`,
`sandbox/` (`grammar/` reserved for future pure-parse fixtures that don't
need evaluation). There is deliberately no separate `.expect.json` /
`.diag.json` split -- one file, one fixture, is more boring and there is
less to keep in sync.

### Parser/evaluator fixtures

```json
{
  "name": "integer division returns float",
  "source": "result = 4 / 2",
  "expect": {
    "type": "entries",
    "value": [
      { "kind": "leaf", "key": "result", "value": { "type": "float", "value": "2.0" } }
    ]
  }
}
```

Or, for a fixture that needs more than one file (`include`):

```json
{
  "name": "include merges into the includer",
  "files": {
    "main.scor": "include \"theme.scor\"\ncolor_name = $accent",
    "theme.scor": "@accent = teal\n"
  },
  "entry": "main.scor",
  "expect": { "type": "entries", "value": [ /* ... */ ] }
}
```

`files`/`entry` is an addition beyond a single `source` string -- needed
because the original three-file-per-fixture idea had nowhere to put a
second `.scor` file, and `include` fixtures need at least two. A fixture
uses exactly one of `source` or `files`+`entry`, never both.

### Runtime options

A parser/evaluator fixture MAY carry an `options` object that overrides only
the limits needed by that fixture:

```json
{
  "name": "loop budget is enforced",
  "source": "while true do\nend",
  "options": { "max_loop_iterations": 16 },
  "expect_error": { "code": "scorium::eval::loop_budget_exceeded" }
}
```

Recognized keys are `max_loop_iterations`, `max_function_call_depth`,
`max_script_instructions`, and `max_script_memory_bytes`. Values are
non-negative JSON integers; all except `max_script_memory_bytes` MUST be
greater than zero. An omitted key uses the implementation's default. This
keeps limit fixtures fast and deterministic without making implementation
defaults part of the language contract.

### Diagnostics fixtures

```json
{
  "name": "undefined interpolation",
  "source": "binding = $nope+Return",
  "expect_error": { "code": "scorium::eval::undefined_interpolation" }
}
```

Only `code` is asserted (§5: codes are the cross-language contract,
message text is not). `source`/`files`+`entry` work the same as above.

### Formatter fixtures

Formatter fixtures do **not** go through the tagged-value encoding at
all -- per §4's unified-output decision, this is a source-to-source
byte-identity check, not a semantic-value check:

```json
{
  "name": "float keeps its decimal point",
  "input": "x = 1.0",
  "output": "x = 1.0\n"
}
```

`output` MUST be produced byte-for-byte identically by every
implementation's `fmt`, and re-formatting `output` MUST reproduce it
exactly (idempotency, §4).

### The `requires` escape hatch

Any fixture MAY carry `"requires": ["lua"]` (default: absent, meaning "no
implementation-capability requirement"). This allows a Lua-dependent fixture
to declare its capability without baking Section 7's unapproved level names
into the schema. No `0.2.0` fixture uses it; the current corpus tests the
language core available without Lua execution.

## Tagged value encoding

Every semantic value (a `Value` per §2 -- not an evaluated document, see
"Entries" below) is `{"type": "<tag>", "value": <encoded>}`:

| tag | value encoding |
|---|---|
| `int` | decimal string, e.g. `"9223372036854775807"`, `"-42"` |
| `float` | decimal/scientific string, or one of the fixed tokens `"nan"`, `"inf"`, `"-inf"` |
| `bool` | JSON `true`/`false` |
| `nil` | no `value` field at all -- just `{"type": "nil"}` |
| `string` | JSON string |
| `color` | `"#RRGGBBAA"`, **always 8 hex digits** (alpha always explicit, even if the source spelled a 6-digit literal with an implied opaque alpha) |
| `duration` | source-style amount+unit string, e.g. `"600ms"`, `"1.5s"`, `"2m"` |
| `list` | `{"type": "list", "value": [<value>, ...]}` |

Naming note: tags use Scorium's own vocabulary (`list`, `nil`), not
JSON's (`array`, `null`) -- this schema describes Scorium values, and using
JSON's own type names for them would blur that distinction. There is
deliberately **no** `object`/map tag: Scorium has no map/object value
type (§2's eight-value list has no such member) -- see "Entries" below for
why a whole evaluated document is not a `Value` at all and must not be
squeezed into one.

**Int and Float are both strings, not JSON numbers** -- this is the same
reasoning as §2's exact-representation requirement: a JSON number is a
`double` in every common JSON library, which cannot exactly carry the
full `Int` range and reintroduces exactly the precision-loss bugs §2
spends a whole section forbidding. Decoding a fixture is expected to
parse these strings with each implementation's own exact `Int`/`Float`
parsing (whatever satisfies §2's exact-representation contract), not a
generic JSON-number decode.

**Value comparison is semantic, not textual -- and it is fixture-assertion
equality, not §2's runtime `==`.** A test harness decodes `expect` into
the implementation's native value representation and structurally
compares it against the actual evaluation result. This is *not* the same
relation as §2's `==` operator: §2 deliberately defines `NaN` as unequal
to everything, including itself (matching Lua/IEEE-754), because that's
the right behavior for a Scorium program comparing two runtime values.
But a fixture asserting "evaluating this produced `NaN`" needs "did I get
the value I expected" -- under which a `NaN` expectation MUST match a
`NaN` result. A harness that reused `==` verbatim for fixture assertions
could never write a passing `NaN`-producing fixture at all. So: ordinary
values compare equal exactly when §2's `==` says so; `NaN`-to-`NaN` is the
one deliberate exception, always a match for fixture purposes.

This is also why ordinary floats need no special canonical form (`"2"`,
`"2.0"`, and `"2.0e0"` are all fine spellings of the same value) -- except
the three special tokens `"nan"`, `"inf"`, `"-inf"`, fixed and
case-sensitive precisely because native float parsers disagree on this
spelling (JavaScript's `parseFloat` accepts `"Infinity"` but not `"inf"`,
for example) -- a harness or adapter MUST special-case exactly these three
tokens rather than hand them to a generic string-to-float parser.

## Entries: the shape of a whole evaluated document

An evaluated Scorium document is **not** a `Value` -- it's an ordered
sequence of entries (leaves, nodes, includes; see `scorium-rs`'s own
three-tier `ast::Item` / `Value` / `Entry` distinction, documented in its
`entry.rs`). Squeezing it into a JSON object (`{"host": ..., "port":
...}`) is tempting for the common case but silently loses two things
Scorium actually allows: **the same node name appearing more than once**
(a JSON object can't have two `"server"` keys), and **node headers**
(`output eDP-1 { ... }`) have nowhere to live in a plain map. The `for`
and `while` fixtures in this batch (`evaluation/for-loop-*.json`,
`evaluation/while-loop-*.json`) exist specifically to prove this isn't
hypothetical -- they each produce three same-named sibling nodes.

So a whole-document (or whole-node-body) result is its own tagged form,
`entries`, an **ordered array**, not a map:

```json
{
  "type": "entries",
  "value": [
    { "kind": "leaf", "key": "port", "value": { "type": "int", "value": "8080" } },
    {
      "kind": "node",
      "name": "server",
      "header": null,
      "children": [ /* nested entries, recursively */ ]
    },
    { "kind": "include", "path": "theme.scor" }
  ]
}
```

`header` is `null` when the node has none, otherwise the header string.

## Version 0.2.0 corpus scope

The `0.2.0` corpus covers pure-language parsing, evaluation, diagnostics,
formatting, and sandbox limits. Host-integration calls and their
implementation-specific result entries are outside this corpus version, so
no `hostcall` entry encoding is defined. A future language version MAY add a
separate host-integration fixture category without changing the meaning of
the `0.2.0` fixtures.

Capability requirements remain a string list rather than named conformance
levels. Section 7 is informative and cannot change how `requires` is decoded.
