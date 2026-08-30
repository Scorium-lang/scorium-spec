# scorium-spec

**Status: draft skeleton. Nothing in this repository is normative yet.**

This repository will hold the versioned Scorium language specification: the
document set that every native implementation (`scorium-rust`, `scorium-go`,
`scorium-jvm`, `scorium-python`, `scorium-dotnet`, `scorium-js`) implements
against, plus a shared conformance fixture corpus each implementation runs in
CI.

Compatibility across implementations comes from this repository, not from
shared source code. Implementations do not share a toolchain, dependencies,
or a release schedule, and are not required to support a new spec version
simultaneously — each one pins and reports the Scorium language version it
supports.

`scorium-rust` (the current Rust codebase) remains the reference
*implementation* while this spec is being written, but its source is not
itself the specification. Where this spec and the reference implementation
disagree once both exist, that is a bug in one of the two, to be resolved
explicitly — not settled by fiat in either direction.

## Layout

- `spec/` — the specification documents, one file per concern. See each
  file's own status line; all are currently outlines, not finished text.
- `conformance/` — versioned fixture corpus (`conformance/<version>/`).
  Each implementation runs the fixtures under the spec version it claims to
  support. See `conformance/README.md` for the proposed fixture format.
- `VERSION` — the current draft spec version.
- `CHANGELOG.md` — spec version history, once versions start shipping.

## Non-goals right now

- No normative grammar/semantics text is finalized.
- No conformance fixtures have been written.
- No decision has been made on the "portable compliance level" (native
  language minus raw `script {}` Lua blocks) described in
  `spec/07-conformance-levels.md` — it is a proposal, not a rule.
