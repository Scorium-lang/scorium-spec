# Changelog

## [0.2.0] - 2026-08-30

First stable language specification. Sections `00`–`06` are normative for
Scorium `0.2.0`; Section `07` remains an informative, unapproved proposal.

Highlights: `%` is defined by a Euclidean-remainder formula independent of
any host language's native operator; `Int`/`Float` comparison and equality
are exact; every implementation represents the complete signed 64-bit `Int`
domain; canonical formatter output is byte-identical across implementations;
and include containment is enforced on canonical, symlink-resolved paths.

The stable contract also defines duration equality and rejects duration
arithmetic/ordering, fixes item and expression evaluation order, rejects
`return` outside a function, makes formatter and Lua-execution capabilities
explicit, defines the Lua sandbox outcome independently of VM module names,
and scopes function-depth counters to one Scorium evaluation.

Added the conformance fixture encoding: tagged semantic values, a dedicated
`entries` shape for whole-document evaluation results, source-to-source byte
fixtures for the formatter, capability requirements, and deterministic
per-fixture runtime-limit options. The versioned corpus contains 34 fixtures
across values, evaluation, diagnostics, formatting, and sandbox behavior.

Prepared the specification as a standalone public repository with shared
project terms, contribution and security guidance, GitHub templates, and
automated validation of version references, fixtures, and documentation
links.

## 0.1.0-draft -- unreleased

Initial skeleton. No normative content yet: section stubs only, seeded from
the current `scorium-rs` documentation (`docs/GRAMMAR.md`,
`docs/LANGUAGE.md`, `docs/DIAGNOSTICS.md`, `docs/ROADMAP.md`) as informative
source material, not as authoritative text.

[0.2.0]: https://github.com/Scorium-lang/scorium-spec/releases/tag/v0.2.0
