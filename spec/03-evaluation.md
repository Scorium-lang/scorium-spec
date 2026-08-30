# 3. Evaluation rules

**Status: stable and normative for language version `0.2.0`. Lua's own
semantics are out of scope; the `script {}` boundary is specified below.
Derived from `scorium-rs` and cross-checked against `scorium-js`.**

## Identifier and interpolation resolution

Covered normatively in §1 (grammar) since it is a name-resolution rule
tied to the `Ident`/`Member` productions: the 5-step priority order
(local/param/loop-var → `@`-variable → sibling leaf → host value → literal
string fallback), and `$name` interpolation having no fallback. Repeated
here only as a cross-reference — do not restate a second, possibly
divergent, version of this rule in an implementation's evaluation code.

## Member access (`base.field`)

A bare `base.field` where `base` resolves to nothing bindable (not a
local/variable/sibling-leaf/host-value) is **not** an error — the whole
`base.field` token is a literal string (this is how dotted bare strings
like `cert.pem` work; see §1). Member access is only ever attempted when
`base` resolves to a real value, and the only value type with fields today
is `Color` via its three methods (§2) — accessed only as a call
(`.darken(x)`), never as a bare field read. A non-call member read
(`color.darken` without `()`), or any member access on a resolved value
that is not `Color`, MUST raise `scorium::eval::type_error`.

## Variable and scope model

- `@name = expr` (`VarDef`) defines a variable visible to later items in
  the same or an enclosing scope. It is **not** reassignable once defined
  (see §1, Reassignment).
- `local name = expr` introduces a lexically scoped binding. A later
  `name = expr` **leaf-shaped** statement where `name` already names a
  `local` in scope reassigns that local instead of emitting a leaf — this
  is the only mutation mechanism in the language (§1).
- Function parameters (`fn f(a, b) { ... }`) are bound as locals in a
  fresh scope pushed for the call; the scope is popped on return
  (normal or via `return`).
- Sibling-leaf access: inside a node body, an earlier leaf's value is
  visible to later expressions in the same body by the leaf's key name,
  at priority 3 in identifier resolution (after locals/params, after
  `@`-variables, before host values).

## Control flow

- `if`/`elseif`/`else`: standard short-circuit evaluation of the first
  matching truthy condition; `else` runs if none matched. Conditions use
  the truthiness rule from §2 (only `Nil`/`false` are falsy).
- Numeric `for var = start, stop[, step] do ... end`: inclusive on both
  ends; default step `1`; a step of exactly `0` (as `Int(0)` or
  `Float(0.0)`) MUST be a `scorium::eval::type_error`, not an infinite
  loop or silent no-op. The loop variable is `Int` when the computed value
  has no fractional part, `Float` otherwise — i.e. its type can vary
  per-iteration if `start`/`stop`/`step` are floats that happen to land on
  whole numbers.
- `while cond do ... end`: re-evaluates `cond` each iteration; ends when it
  is falsy.
- `and`/`or` are short-circuiting and return one of their two operand
  values (not necessarily a `Bool`) — `Lua`-style: `a or b` yields `a` if
  `a` is truthy, else evaluates and yields `b`; `a and b` yields `a` if `a`
  is falsy, else evaluates and yields `b`.
- `return [expr]` exits the innermost executing Scorium function with that
  value (`Nil` if omitted), including from nested control flow or a node body.
  Evaluating `return` while no Scorium function call is active MUST raise
  `scorium::eval::return_outside_function`.

## Evaluation order

Documents, node bodies, and executed control-flow bodies evaluate items in
source order. A node header is a literal string, not an expression, so it has
no evaluation effects. The node body is evaluated before its resulting node
entry is appended to the parent output.

Expression operands and function arguments evaluate left to right. The only
operator exceptions are `and` and `or`, which evaluate the right operand only
when required by their short-circuit rules. An `include` executes at its
source position before evaluation continues with the following item.

## Resource limits (sandbox knobs, evaluation-visible)

Every evaluator MUST expose the first two limits below as host-settable knobs
and enforce them. An implementation that executes `script {}` MUST also
expose and enforce the two script-runtime limits:

- **Loop iterations** — total `for`/`while` iterations allowed across one
  evaluation. `scorium-rs` default: `1_000_000`. Exceeding it MUST
  raise `scorium::eval::loop_budget_exceeded`, naming the limit.
- **Evaluation/call depth** — maximum nesting depth for `fn` calls.
  `scorium-rs` default: `256`. Exceeding it MUST raise
  `scorium::eval::call_depth_exceeded`, naming the limit.
- **Script instruction count** — VM instructions allowed per `script {}`
  block. `scorium-rs` default: `50_000_000`. Exceeding it MUST raise
  `scorium::eval::script_error`.
- **Script memory** — bytes the script runtime may allocate. `scorium-rs`
  default: `64 MiB`; `0` disables the cap. Exceeding a nonzero cap MUST raise
  `scorium::eval::script_error`.

The existence and configurability of the applicable limits and their defined
diagnostics are normative. The specific default numbers are informative; an
implementation MAY ship different defaults. Conformance fixtures that depend
on a limit set it explicitly through the fixture `options` object and never
assume an implementation default.

A native implementation embedding a runtime without these checks (e.g.
relying on the host language's own stack limit for recursion instead of
an explicit call-depth counter) is not conformant even if it happens not
to crash on the conformance fixtures, since the diagnostic on exceeding
the limit is itself part of the observable, testable contract.

### Function-depth budget boundary

The function-depth limit counts active Scorium `fn` calls within one
evaluation. Lua VM frames do not consume this counter; they are bounded by the
script instruction and memory limits. If a host callback starts a new Scorium
evaluation, that evaluation owns a new function-depth counter. Hosts that
permit arbitrary mutual re-entry are responsible for applying an additional
outer re-entry limit appropriate to their capability model.

## `include`

- Resolves relative to `base_dir` (typically the including file's
  directory).
- Cycle detection: an include chain that would revisit a file already in
  the current inclusion stack MUST raise `scorium::eval::include_cycle`
  with the chain listed.
- Path policy (host-configurable, see §6): by default, parent-directory
  traversal (`..` components), absolute paths, and symlink escapes outside
  the allowed root are denied — `scorium::eval::include_path_denied`.
  A host may disable `include` entirely — `scorium::eval::includes_disabled`.
- I/O or parse failure on the included file surfaces as
  `scorium::eval::include_io` / `scorium::eval::include_parse` respectively,
  distinct from the two policy errors above.

## `script {}` boundary

When supported, `script {}` bodies are raw Lua executed by an embedded Lua VM
under the sandbox limits in §6. This document does not specify Lua's own
semantics — only the boundary contract:

- Host functions/values registered through the shared registry (§6) MUST
  be reachable identically from both plain Scorium expressions and
  `script {}` bodies.
- A runtime failure inside a script body surfaces as
  `scorium::eval::script_error` with the underlying message, not a raw,
  implementation-specific Lua error type leaking through.
- An implementation without Lua execution MUST raise
  `scorium::eval::script_error` when evaluation reaches a script block and
  MUST NOT execute it as another language, silently skip it, or treat it as a
  no-op.
