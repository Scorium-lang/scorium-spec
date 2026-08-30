# 3. Evaluation rules

**Status: first full draft, language version `0.1.0-draft`. Normative for
the Portable level (see §7); `script {}` execution semantics belong to Lua
itself and are out of scope here beyond the boundary rules stated below.
Derived from `crates/scorium-lua/src/eval.rs` and `runtime.rs`.**

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
- `return [expr]` inside a `fn` body exits with that value (`Nil` if
  omitted); outside a function body `return` is a parse-time construct
  only reachable inside `fn` (grammar-level, not evaluation-level,
  restriction — to be confirmed and pinned down in §1 once verified).

## Resource limits (sandbox knobs, evaluation-visible)

Four **required configurable limits** — every implementation MUST expose
each as a host-settable knob and MUST enforce it, regardless of what
default value it picks:

- **Loop iterations** — total `for`/`while` iterations allowed across one
  evaluation. `scorium-rust` default: `1_000_000`. Exceeding it MUST
  raise `scorium::eval::loop_budget_exceeded`, naming the limit.
- **Evaluation/call depth** — maximum nesting depth for `fn` calls.
  `scorium-rust` default: `256`. Exceeding it MUST raise
  `scorium::eval::call_depth_exceeded`, naming the limit.
- **Script instruction count** — VM instructions allowed per `script {}`
  block (Full-level implementations only, §7). `scorium-rust` default:
  `50_000_000`.
- **Script memory** — bytes the script runtime may allocate (Full-level
  only). `scorium-rust` default: `64 MiB`, `0` disables the cap.

The existence of these four limits, the requirement that a host can
configure each, and the requirement that exceeding one produces the
defined diagnostic (not a crash, hang, or silent truncation) are
normative — the *specific default numbers* are not: an implementation MAY
ship different defaults. A future **compatibility profile** concept — a
named, spec-defined set of pinned default values implementations can
opt into for byte-for-byte behavioral comparison across languages — is
worth considering once there's a concrete cross-implementation testing
need for it, but is not defined in `0.1.0-draft`.

A native implementation embedding a runtime without these checks (e.g.
relying on the host language's own stack limit for recursion instead of
an explicit call-depth counter) is not conformant even if it happens not
to crash on the conformance fixtures, since the diagnostic on exceeding
the limit is itself part of the observable, testable contract.

### Open: shared vs. independent depth budgets across the Lua boundary

Undecided. If a Scorium `fn` call reaches into a `script {}` body (via a
host-registered Lua function, say) which itself calls back into Scorium
evaluation (e.g. by invoking a host function that re-enters the
evaluator), does that recursion draw from **one shared** call-depth
budget across both the Scorium and Lua sides, or **two independent**
budgets (a Scorium `fn`-depth counter and a separate Lua call-depth
counter)? `scorium-rust`'s current `max_function_call_depth` only counts
`call_user_fn` (pure Scorium `fn` recursion) — it does not appear to
account for depth contributed by a round-trip through Lua at all, which
means a Scorium→Lua→Scorium cycle could exceed any *intended* combined
depth limit without tripping either counter. This needs a real decision,
not an assumption, before `0.1.0`: a single shared budget is simpler to
reason about and closes this gap directly; two independent budgets are
easier to implement per-side but require an explicit design for how (or
whether) they interact.

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

`script {}` bodies are raw Lua, executed by an embedded Lua VM under the
sandbox limits in §6. This document does not specify Lua's own semantics
(that's Lua's job) — only the boundary contract:

- Host functions/values registered through the shared registry (§6) MUST
  be reachable identically from both plain Scorium expressions and
  `script {}` bodies.
- A runtime failure inside a script body surfaces as
  `scorium::eval::script_error` with the underlying message, not a raw,
  implementation-specific Lua error type leaking through.
- Per §7 (conformance levels, proposal), a Portable-level implementation
  that does not embed Lua MUST still parse `script {}` correctly (§1) and
  raise a defined, distinct diagnostic when one is encountered at
  evaluation time — never silently skip the block or treat its body as a
  no-op.

## Open questions

- Exact evaluation order guarantees beyond what's stated above (e.g.
  whether a node's header expression evaluates before or interleaved with
  its first body item) are not yet pinned down and need conformance
  fixtures that would actually distinguish the orders before they can be
  made normative.
- Whether `return` outside a `fn` body is a grammar-level parse error or
  an evaluation-level error is unconfirmed against `scorium-rust`'s actual
  behavior (see inline note above).
