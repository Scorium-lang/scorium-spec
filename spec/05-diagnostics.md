# 5. Diagnostic model

**Status: stable for language version `0.2.0`. The code catalog and minimum
structure below are normative; message text and rendering are not. Derived
from `crates/scorium-core/src/diagnostic.rs` (lex/parse),
`crates/scorium-lua/src/error.rs` (eval), and
`crates/scorium-schema/src/error.rs` (schema).**

## What's normative vs. not

- **Diagnostic codes** (`scorium::<stage>::<name>`) are the cross-language
  contract. Tooling and tests branch on codes, not message text — every
  implementation MUST emit the same code for the same fault condition.
- **Message text, help text, and rendering** (`scorium-rs` uses `miette`
  for source excerpts, carets, and boxes) are implementation presentation.
  A different implementation is free to render differently, or to
  translate message text, as long as the code and the required structured
  fields (below) are present.
- Fields beyond the minimum structure below, such as `name` and
  `suggestion`, are optional implementation metadata in `0.2.0` unless the
  code catalog explicitly requires them.

## Required structure

Every diagnostic MUST carry, at minimum:

- a stable **code** in the `scorium::<stage>::<name>` namespace;
- a **span** (or spans, for a diagnostic with a related secondary
  location, e.g. duplicate-key's "first set here") locating the fault in
  source;
- a human-readable **message**.

## The explicit-error requirement

Restated from the multi-language discussion because it is easy to violate
silently in a new implementation: any construct an implementation does not
support (including `script {}` execution in an implementation without Lua)
MUST raise a diagnostic with a defined code. Silently
ignoring, no-op'ing, or best-effort-guessing a value for an unsupported
construct is non-conformant regardless of how reasonable the guess is.

## Code catalog (language version `0.2.0`)

### `scorium::lex::*`

| code | condition |
|---|---|
| `scorium::lex::unexpected_char` | a character not valid at the current lexer position |
| `scorium::lex::unterminated_string` | `"..."` never closed before EOF/newline |
| `scorium::lex::unterminated_comment` | `--[[...` never closed with `]]` before EOF |
| `scorium::lex::squeezed_operator` | a binary operator missing required surrounding spaces (§1) |

### `scorium::parse::*`

| code | condition |
|---|---|
| `scorium::parse::unexpected_token` | token found where a different one was required |
| `scorium::parse::at_in_expression` | `@name` used inside an expression rather than on its own definition line |
| `scorium::parse::dollar_in_expression` | `$name` used inside an expression rather than inside a bare string |
| `scorium::parse::reserved_word` | a reserved word (§1) used as a node name |
| `scorium::parse::unexpected_eof` | input ended mid-construct |

### `scorium::eval::*`

| code | condition |
|---|---|
| `scorium::eval::undefined_interpolation` | `$name` with no matching `@`-variable |
| `scorium::eval::unknown_function` | a call to a name that is neither a host function nor a Scorium `fn` |
| `scorium::eval::return_outside_function` | `return` evaluated while no Scorium function call is active |
| `scorium::eval::type_error` | an operation applied to a value type it doesn't support (arithmetic, comparison, member access, call arity/type) |
| `scorium::eval::division_by_zero` | `/` or `%` with a zero divisor |
| `scorium::eval::arithmetic_overflow` | checked integer `+ - *` (or unary `-`) overflows `i64` range |
| `scorium::eval::includes_disabled` | `include` used while the host has disabled it |
| `scorium::eval::include_path_denied` | an include path violates the host's traversal policy |
| `scorium::eval::include_cycle` | see note above |
| `scorium::eval::include_io` | the included file could not be read |
| `scorium::eval::include_parse` | the included file failed to parse |
| `scorium::eval::script_error` | script execution is unsupported, failed, or exceeded a script-runtime limit |
| `scorium::eval::loop_budget_exceeded` | total loop iterations exceeded the configured limit |
| `scorium::eval::call_depth_exceeded` | `fn` call nesting exceeded the configured limit |

### `scorium::schema::*`

| code | condition |
|---|---|
| `scorium::schema::unknown_node` | a node name not declared in the schema (may carry a typo `suggestion`) |
| `scorium::schema::unknown_key` | a leaf key not declared for its node (may carry a typo `suggestion`) |
| `scorium::schema::wrong_type` | a value's type doesn't match the schema's declared type for that key |
| `scorium::schema::missing_required_key` | a required key absent from a node |
| `scorium::schema::duplicate_key` | the same key set twice in one node (carries both the duplicate and first-occurrence spans) |
| `scorium::schema::invalid_header` | a node header fails host-defined header validation |

## Resolved: `include::cycle` vs. `eval::include_cycle`

`scorium-rs` defines two include-cycle diagnostic variants:
`SyntaxError::IncludeCycle` (`scorium::include::cycle`, in
`scorium-core/src/diagnostic.rs`) and `EvalErrorKind::IncludeCycle`
(`scorium::eval::include_cycle`, in `scorium-lua/src/error.rs`). Checking
actual usage: only `EvalErrorKind::IncludeCycle` is ever constructed;
`SyntaxError::IncludeCycle` is dead code in that implementation — defined
but never raised. This is not
two distinct real conditions, just one live diagnostic and one vestigial
duplicate.

**Normative for `0.2.0`: `scorium::eval::include_cycle` is the only
include-cycle code.** `scorium::include::cycle` MUST NOT be treated as
part of the spec — a new implementation should not invent a
parse-time-vs-eval-time distinction here that doesn't actually exist in
the verified behavior. (Separately, `scorium-rs` itself carries dead
code defining the unused variant — worth a small cleanup there at some
point, but that's a `scorium-rs` housekeeping change, not a spec
concern, and out of scope for this specification version.)

## Message language and additional fields

Implementations MAY localize diagnostic messages and help text. Codes remain
ASCII and stable across locales. Additional structured fields are encouraged
for tooling but are not cross-language conformance requirements in `0.2.0`,
except that `duplicate_key` carries both relevant spans as stated above.
