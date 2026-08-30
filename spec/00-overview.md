# 0. Overview

**Status: Design principle below is settled; the rest of this file is
still outline only.**

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

This matters directly for how the rest of this document, especially §7
(conformance levels), should be read: the native evaluation model in §3
— variables, expressions, conditionals, loops, user-defined `fn` — is
**not** a lesser subset bolted on for portability's sake. It *is* the
"becomes programmable" half of the core value proposition, and every
implementation gets it natively, in its own language, with no embedded
VM required. Raw `script {}` (Lua, §6) is an escape hatch beyond that —
useful, and part of "Full" conformance — but an implementation that only
reaches "Portable" has still delivered the actual design principle above,
not a crippled placeholder waiting for Lua support. Language work
(spec sections, conformance fixtures, implementation priority) should
keep optimizing for this progressive readable-to-programmable path, not
treat raw scripting as the feature the rest of the language merely leads
up to.

## What this spec must eventually pin down

- The name and version scheme for the language itself, independent of any
  implementation's own release version (e.g. `scorium-rust` 0.1.0 implementing
  language version `0.1.0-draft`).
- Which sections are normative (MUST-level, testable by conformance
  fixtures) versus informative (rationale, examples).
- The relationship between this spec and `scorium-rust`: the Rust
  implementation is the current reference implementation and initial source
  of ground truth, but this document — once versioned 1.0 — is the
  authority implementations conform to, not the Rust source.

## Open questions

- RFC-style change process for the spec itself has not been decided.
- Whether pre-1.0 spec versions carry any compatibility guarantee at all,
  or are explicitly "may change under you" until 1.0.
