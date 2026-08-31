# Roadmap

Scorium's roadmap is organized around user workflows, not feature count. A
configuration should behave the same when a host moves between Rust,
JavaScript, and Go. API spelling remains idiomatic to each language. Rust's
sandboxed Lua capability is intentionally optional at the language-family
level; JavaScript and Go reject `script {}` explicitly.

## 1. Lock the behavior

Delivered in language version `0.2.1`.

- 56 shared fixtures cover values, evaluation, diagnostics, formatting,
  sandbox limits, include policy, capability gates, and schema validation.
- Fixtures declare required and excluded capabilities instead of pretending
  every runtime embeds Lua.
- Diagnostic codes and deterministic schema errors are portable contracts.

## 2. Make every port feel like Scorium

Delivered across `scorium-rs`, `scorium-js`, and `scorium-go`.

- Reserved words, string escapes, include failures, headers, duplicates, and
  suggestions now follow the same behavior.
- Native APIs stay idiomatic; semantic results and errors stay equivalent.
- Unsupported `script {}` execution is an explicit diagnostic in non-Lua
  ports, never a skipped block.

## 3. Stabilize the tool boundary

Delivered as [tooling contract v1](./tooling/README.md).

- All CLIs share `check`, `parse`, `fmt`, and `eval` behavior and exit status.
- `check --json` emits stable diagnostic envelopes with UTF-16 LSP ranges.
- `parse --json` emits one portable syntax tree shape across all ports.
- `eval --json` continues to use the conformance tagged-value encoding.

## 4. Shorten the host integration path

Delivered with high-level file and source loaders in all three ports.

- Loaders retain source names, derive the include base from the file, and
  return both the native document and evaluated entries.
- Lower-level parse, evaluate, schema, and format APIs remain available.
- Safe include and sandbox defaults apply without host boilerplate.
- All three ports also accept a host-supplied `IncludeResolver` that
  overrides filesystem-backed `include` resolution entirely, for content
  addressed by URL, stored in a database, or held as unsaved editor
  buffers. Built ahead of a concrete consumer, on explicit request rather
  than observed friction -- an exception to this roadmap's own
  evidence-first default, not a new default way of working.

## 5. Put diagnostics in the editor

Delivered first as the Rust `scorium-lsp` executable.

- Live syntax diagnostics use stable Scorium codes and UTF-16 ranges.
- Once syntax is valid, evaluation runs too (no host functions/values, no
  application schema), catching undefined interpolation, unknown
  functions, division by zero, include failures, sandbox-limit overruns,
  and `script {}` bodies through the same sandboxed Lua state
  `scorium`/`scorium-lua` hosts use.
- Whole-document formatting uses the canonical formatter.
- Host-schema-aware diagnostics were deliberately not added: there is no
  schema description format for a generic editor server to load without
  recreating exactly the schema-language problem this project has
  declined to solve speculatively (`scorium-schema`'s own doc comment).
  Application-schema checks remain an explicit host operation.

One language server serves `.scor` files produced by any host. Duplicating an
LSP per implementation would create drift without improving user behavior.

## 6. Prove the integration in a real host

Delivered through AquaTTY.

- AquaTTY's private subset parser was replaced by `scorium-go` while its
  application-specific settings mapping stayed in the application.
- Expressions, variables, functions, control flow, and contained includes are
  available without adding Lua.
- The existing hot-reload and validation paths continue to pass their full
  application test suite.

## What comes next

`IncludeResolver` and `docs/API_STABILITY.md` (stability tiers, deprecation
policy, upgrade guidance) landed in all three ports; `scorium-lsp` gained
evaluation diagnostics without inventing a schema description format. Future
work should still start from observed friction in editors and host
applications, not from this list. New syntax, a schema language, generic
iteration, and extra runtime capabilities remain deferred until a real user
workflow cannot be handled cleanly by Scorium's existing model.
