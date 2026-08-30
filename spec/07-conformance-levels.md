# 7. Conformance levels

**Status: informative proposal only. It is not part of stable language
version `0.2.0` and does not define a conformance claim.**

This section records a design discussed for making Scorium portable to
languages without a practical embedded-Lua story, without inventing a
different language per platform.

## The problem

`scorium-rs`'s evaluator already interprets expressions, variables,
conditionals, loops, and user-defined functions natively in Rust — only
raw `script {}` blocks require an actual Lua VM (`scorium-lua`, via
`mlua`). A pure Go/JVM/Python/.NET/JS implementation can plausibly
reimplement all of that native evaluation without embedding Lua at all,
*except* `script {}`, which fundamentally requires a Lua runtime in the
target language.

## Proposed model

Two conformance levels:

- **Portable** — the full native language (§1–4, §6 minus the Lua-specific
  sandbox rules) with `script {}` unsupported.
- **Full** — Portable plus `script {}`, requiring an embedded Lua VM in the
  implementation's own language runtime (e.g. a pure-Go Lua VM for
  `scorium-go`), explicitly still native — never a wrapper around
  `scorium-rs`'s Lua integration.

Under this proposal, an implementation would declare which level it claims.
The stable `0.2.0` rule already requires an implementation without Lua
execution to raise `scorium::eval::script_error` when evaluation reaches a
script block; it may not skip the block or treat it as inert (§1, §3, §5).

## Open questions (blocking approval)

- Whether "Portable" is actually sufficient for real consumers, or whether
  most real-world Scorium configs lean on `script {}` enough that a
  Portable-only implementation is not useful in practice — unknown until
  `scorium-go` is built against a real consumer (AquaTTY).
- Whether there should be a third level between them (e.g. a restricted
  expression sandbox short of full Lua) — no evidence yet that this is
  needed.
- Naming: "Portable"/"Full" are placeholders, not decided terms.
