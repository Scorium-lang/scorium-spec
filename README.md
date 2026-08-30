# Scorium language specification

[![CI](https://github.com/Scorium-lang/scorium-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/Scorium-lang/scorium-spec/actions/workflows/ci.yml)
[![Language version](https://img.shields.io/badge/language-0.2.0-8EDDFF?style=flat-square)](./VERSION)
[![Status](https://img.shields.io/badge/status-stable%20pre--1.0-8EDDFF?style=flat-square)](./CHANGELOG.md)
[![Source Available](https://img.shields.io/badge/source-available-8EDDFF?style=flat-square)](./LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Scorium-lang/scorium-spec?style=flat-square&logo=github)](https://github.com/Scorium-lang/scorium-spec/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/Scorium-lang/scorium-spec?style=flat-square&logo=github)](https://github.com/Scorium-lang/scorium-spec/issues)

**Readable on the surface. Programmable when you need it.**

This repository is the implementation-independent specification for the
Scorium configuration language. It defines the grammar, value semantics,
evaluation rules, canonical formatting, diagnostics, sandbox requirements,
and the shared conformance fixtures used by native implementations.

When an implementation disagrees with this specification, the disagreement
must be resolved explicitly. An implementation's source code does not
silently override the language contract.

```scor
@base_port = 8000

server {
    host = localhost
    port = base_port + 80
    timeout = 5s
    enabled = true
}

for i = 1, 3 do
    worker {
        name = worker-$i
        index = i
    }
end
```

## Current status

The current language version is **`0.2.0`**. Sections 0–6 are stable and
normative for that version, grounded in the Rust reference implementation and
cross-checked with the native TypeScript implementation. Section 7 is an
informative, unapproved proposal and is not part of the language contract.

The repository contains **34 conformance fixtures** across values,
evaluation, diagnostics, formatting, and sandbox behavior. Scorium remains
pre-1.0, so a future minor language version may make incompatible changes;
version `0.2.0` itself is no longer a draft.

## Specification

- [Overview and design principle](./spec/00-overview.md)
- [Lexical structure and grammar](./spec/01-lexical-and-grammar.md)
- [Value semantics](./spec/02-value-semantics.md)
- [Evaluation rules](./spec/03-evaluation.md)
- [Canonical formatter behavior](./spec/04-formatter.md)
- [Diagnostic model](./spec/05-diagnostics.md)
- [Sandbox and security rules](./spec/06-sandbox-and-security.md)
- [Conformance-level proposal](./spec/07-conformance-levels.md)

## Conformance fixtures

Fixtures live under `conformance/v<language-version>/`. Each implementation
runs the directory matching the language version it claims to support. The
fixture format uses tagged semantic values so integers, floating-point edge
cases, repeated nodes, and formatter byte identity remain unambiguous across
host languages.

See [the conformance format](./conformance/README.md) before implementing a
harness or contributing a fixture. Compatibility comes from these fixtures,
not from implementations sharing source code or release schedules.

## Implementations

- [`scorium-rs`](https://github.com/Scorium-lang/scorium-rs) — Rust reference
  implementation, including the Lua execution surface.
- [`scorium-js`](https://github.com/Scorium-lang/scorium-js) — native
  TypeScript/JavaScript implementation of the non-Lua language core.

An implementation version and a language version are separate. For example,
an implementation may release version `0.9.0` while declaring support for
language version `0.2.0`.

## Repository layout

- `spec/` — one specification document per language concern.
- `conformance/` — fixture format and versioned fixture corpora.
- `VERSION` — current language version.
- `CHANGELOG.md` — language-version history.

## Contributing and security

Read [CONTRIBUTING.md](./CONTRIBUTING.md) before proposing normative changes
or fixtures. Report security-sensitive specification flaws privately as
described in [SECURITY.md](./SECURITY.md).

Scorium is source-available under PolyForm Strict 1.0.0; it is **not**
OSI-approved open source. See [LICENSE](./LICENSE) and
[COMMERCIAL.md](./COMMERCIAL.md).
