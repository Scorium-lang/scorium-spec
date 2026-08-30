# 6. Sandbox and security rules

**Status: stable and normative for language version `0.2.0`.
Derived from `crates/scorium-lua/src/runtime.rs`.**

## Resource limits

Every evaluator MUST expose and enforce the loop and function-depth limits as
host-configurable knobs. An evaluator that executes `script {}` MUST also
expose and enforce the script instruction and Lua memory limits. Names below
are concepts, not required API identifier spellings:

| limit | `scorium-rs` default | enforcement |
|---|---|---|
| loop budget (total `for`/`while` iterations per evaluation) | 1,000,000 | `scorium::eval::loop_budget_exceeded` |
| function call depth (`fn` nesting) | 256 | `scorium::eval::call_depth_exceeded` |
| script instruction budget (Lua VM instructions per `script {}`, only relevant when Lua execution is supported) | 50,000,000 | script execution aborts; surfaces as `scorium::eval::script_error` |
| Lua memory limit (bytes the Lua state may allocate; `0` disables it) | 64 MiB | Lua allocation failure surfaces as `scorium::eval::script_error` |

These are `scorium-rs`'s current default values, listed here as
reasonable starting points, not as fixed normative numbers -- see §3 for
the full statement of what's normative (the limit's existence,
configurability, and error path) versus what's an implementation choice
(the default value). A future named **compatibility profile** could pin
these defaults for cross-implementation comparison, but no such profile
is defined in `0.2.0`.

## Lua sandbox scope

`scorium-rs` runs `script {}` in a restricted Lua state exposing only
`math`, `string`, and `table` from the standard library -- explicitly
**not** `io`, `os`, `package`, `debug`, or any process/network access.

The security outcome is normative, not the Lua VM's module names. A script
MUST NOT gain filesystem, process, network, unrestricted environment,
dynamic native-module loading, or debug-introspection capability except
through a host function deliberately registered as such. Exposing only
`math`, `string`, and `table` is one conforming allowlist; another Lua VM MAY
organize safe primitives differently while preserving the same outcome.

## Host function/value registry

A single registry mechanism registers host functions and values. They are
reachable from plain Scorium expressions (`f(a, b)`, bare identifier
reference) and, when Lua execution is supported, from `script {}` bodies --
"one registry, multiple surfaces." A Lua-capable implementation MUST preserve
this property: a host function registered once is callable from both surfaces
without separate registration. An implementation without Lua execution still
MUST provide the plain-expression registry surface.

## `include` path policy

Default policy (`IncludePolicy` in `scorium-rs`):

- `include` is enabled by default; a host MAY disable it entirely
  (`scorium::eval::includes_disabled`).
- Parent-directory traversal (`..` path components) is **rejected** by
  default; a host MAY opt in to allowing it.
- Absolute paths and symlink escapes outside the allowed root are rejected
  regardless of the traversal setting -- these are not covered by the
  `allow_parent_traversal` opt-in and MUST remain denied by default in
  every implementation.
- Cycle detection is independent of path policy and always active (§3).

**Containment is normative, and MUST be enforced on the canonical
(resolved) path, never the textual path.** This is not an implementation
detail left to each host -- it is a security property every conforming
implementation MUST provide identically:

1. Reject a textual `..` component or an absolute path outright (cheap,
   pre-filesystem check) unless the host has opted into
   `allow_parent_traversal`.
2. Independently -- because a purely relative, `..`-free path can still
   escape through a symlink -- canonicalize both the include root
   (`base_dir`) and the resolved target path (resolving all symlinks,
   including a chain of them), then require the canonical target to be
   contained within the canonical root (`target.starts_with(root)` on the
   canonicalized forms). A target that escapes the root through *any*
   number of intermediate symlinks MUST be denied, exactly as if it had
   used a literal `..`.

Concretely: given a root at `root/` containing `root/config.sc`, an
`include "../secret.sc"` MUST be denied after canonicalization -- and so
MUST an `include "safe.sc"` where `root/safe.sc` is itself a symlink
resolving outside `root/`, even though its literal path contains no `..`
and is not absolute. Implementations MUST NOT rely on textual path
inspection alone; symlink-based containment bypass is exactly the failure
mode canonicalization exists to close. `scorium-rs`'s `exec_include`
(`crates/scorium-lua/src/eval.rs`) implements this two-step check and is
the reference for the algorithm.

## Implementations without Lua execution

An implementation without `script {}` execution has no Lua sandbox surface,
but still owns every other rule in this section. Include path policy, loop
budget, and function-call depth are language-core requirements. Section 7's
possible conformance-level names do not change the `0.2.0` requirements.
