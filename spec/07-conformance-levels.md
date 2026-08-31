# 7. Conformance levels

**Status: informative proposal only. It is not part of stable language
version `0.2.1` and does not define a conformance claim.**

This section records a design discussed for making Scorium portable to
languages without a practical embedded-Lua story, without inventing a
different language per platform.

## The problem

`scorium-rs`'s evaluator already interprets expressions, variables,
conditionals, loops, and user-defined functions natively in Rust -- only
raw `script {}` blocks require an actual Lua VM (`scorium-lua`, via
`mlua`). A pure Go/JVM/Python/.NET/JS implementation can plausibly
reimplement all of that native evaluation without embedding Lua at all,
*except* `script {}`, which fundamentally requires a Lua runtime in the
target language.

## Proposed model

Two conformance levels:

- **Core** -- the full native language (§1-4, §6 minus the Lua-specific
  sandbox rules) with `script {}` unsupported.
- **Full** -- Core plus `script {}`, requiring an embedded Lua VM in the
  implementation's own language runtime (e.g. a pure-Go Lua VM for
  `scorium-go`), explicitly still native -- never a wrapper around
  `scorium-rs`'s Lua integration.

Under this proposal, an implementation would declare which level it claims.
The stable `0.2.1` rule already requires an implementation without Lua
execution to raise `scorium::eval::script_error` when evaluation reaches a
script block; it may not skip the block or treat it as inert (§1, §3, §5).

If an implementation later adds Full-level support after shipping Core,
that support SHOULD be an optional capability a consumer opts into (a
separate package/module, a build feature, or equivalent), not something
that becomes a dependency of the base Core package -- a consumer who only
needs Core shouldn't have to carry a Lua VM to get it. This is packaging
guidance for implementations, not a normative requirement of this
still-informative section.

## Current status (informative, not an approval)

`scorium-js` has decided to stay at Core scope for now -- no `script {}`
execution is planned there until there's real evidence it's worth adding.
`scorium-go` is the designated vehicle for gathering that evidence: build
it Core-only, run it against a real consumer (AquaTTY), and see whether
Core alone is actually sufficient in practice. This doesn't resolve the
open questions below -- it's how they'll get resolved.

## Open questions (blocking approval)

- Whether Core is actually sufficient for real consumers, or whether
  most real-world Scorium configs lean on `script {}` enough that a
  Core-only implementation is not useful in practice -- being tested via
  `scorium-go` against AquaTTY (see "Current status" above).
- Whether there should be a third level between them (e.g. a restricted
  expression sandbox short of full Lua) -- no evidence yet that this is
  needed.
- Naming: "Core" is the working name for the no-Lua level; "Full" remains
  a placeholder, not a decided term.
