# 0. Overview

**Status: stable and normative for language version `0.2.0`, except where a
section is explicitly marked informative or out of scope.**

## Purpose

Defines what "Scorium" means independent of any one implementation.

## Design principle

The interesting, load-bearing idea of the language — the thing every
section below exists to serve, not just one feature among many — is:

**readable configuration that can become programmable when needed,
without switching formats.**

A beginner writes plain, static config (nodes, leaves, typed values — §1,
§2) and never needs to know the language has a programming model at all.
An advanced user reaches for variables, expressions, conditions, loops,
and functions (§3) directly in the same file, in the same syntax, without
migrating to a different config format or a general-purpose language to
get there. That progressive path — declarative first, programmable on
demand, one format throughout — is what distinguishes Scorium from both
"just a data format" (JSON/YAML/TOML) and "just an embedded scripting
language with config-shaped output."

This matters directly for how the rest of this document should be read: the
native evaluation model in §3
— variables, expressions, conditionals, loops, user-defined `fn` — is
**not** a lesser subset bolted on for portability's sake. It *is* the
"becomes programmable" half of the core value proposition, and every
implementation gets it natively, in its own language, with no embedded
VM required. Raw `script {}` (Lua, §6) is an escape hatch beyond that —
useful, but an optional execution capability in version `0.2.0`. An
implementation without Lua execution has still delivered the actual design
principle above, not a crippled placeholder waiting for Lua support. Language
work (spec sections, conformance fixtures, implementation priority) should
keep optimizing for this progressive readable-to-programmable path, not treat
raw scripting as the feature the rest of the language merely leads up to.

## Authority and normative scope

Sections 0–6 are the language contract for `0.2.0`. Statements using
**MUST**, **MUST NOT**, **SHOULD**, or **MAY** are normative. Rationale,
implementation examples, roadmap notes, and text explicitly labelled
informative are not normative. Section 7 is an informative proposal and is
not part of `0.2.0` conformance.

No host-language implementation is the reference or authority for Scorium.
This versioned specification and its conformance fixtures define the shared
contract. A divergence is a bug in the specification, fixtures, or an
implementation that must be resolved explicitly; implementations must not
silently copy a different behavior.

## Versioning and compatibility

Language versions use Semantic Versioning independently of implementation
package versions. For example, `scorium-rs` 0.1.1 may implement language
version `0.2.0`.

Before language version 1.0, a minor version MAY make incompatible language
changes. A patch version MUST preserve valid programs and their observable
behavior, except when correcting a security flaw or an internally
contradictory rule that cannot be preserved safely. Additive clarifications
and new fixtures for already-required behavior normally use a patch version.

Changes are proposed and reviewed through GitHub issues and pull requests as
described in `CONTRIBUTING.md`. A separate RFC document format is not required
for `0.2.0`; a future process change does not alter this language version.
