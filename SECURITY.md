# Security Policy

## Reporting a vulnerability

Do not open a public issue for a security-sensitive flaw. Open a private
[GitHub Security Advisory](https://github.com/Scorium-lang/scorium-spec/security/advisories/new)
or contact [@fi3w0](https://github.com/Fi3w0) privately on GitHub.

Include the affected specification section or fixture, the unsafe behavior
it permits or requires, affected implementations if known, and the smallest
demonstration you can provide. Do not include live credentials or private
user data.

## Scope

This repository contains documents and test fixtures rather than an
executable parser or evaluator. A specification issue is nevertheless
security-sensitive when following the written rule could make conforming
implementations unsafe. Examples include:

- sandbox wording that permits filesystem, process, network, environment, or
  native-module access that should be denied;
- include rules that allow traversal, symlink escape, or cycle bypass;
- resource-limit rules that permit unbounded evaluation;
- ambiguous requirements likely to produce a cross-implementation sandbox
  bypass; or
- a conformance fixture that exposes sensitive data or requires unsafe
  behavior.

Bugs in a particular implementation that do not arise from this language
contract should be reported privately to that implementation's repository.

## Supported versions

The latest language version on `main` receives security corrections. Earlier
versions and historical tags do not currently receive backports.

Security corrections may intentionally land with limited detail until
affected implementations have had a reasonable opportunity to update.

---

**Legal notice.** This policy is operational guidance, not a warranty of any
level of security. It has not been reviewed by a lawyer.
