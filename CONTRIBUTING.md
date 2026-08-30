# Contributing to the Scorium specification

Thank you for helping make Scorium precise and portable. This repository is
the language contract shared by every implementation, so even small wording
changes can have cross-language consequences.

Before contributing, read [CONTRIBUTION_PERMISSION.md](./CONTRIBUTION_PERMISSION.md)
and [CONTRIBUTOR_TERMS.md](./CONTRIBUTOR_TERMS.md).

## Good contributions

- Clarify an ambiguity without changing intended behavior.
- Add a conformance fixture for behavior already specified.
- Report a mismatch between the specification and an implementation.
- Improve examples, terminology, navigation, or diagnostics.
- Propose a language change with its compatibility and security impact.

Open an issue before a large normative change. Section 7's conformance-level
model remains an unapproved proposal; a contribution must not present it as
settled without an explicit project decision.

## Preparing a change

1. Fork the repository for the purpose of contributing upstream.
2. Create a focused branch.
3. Make one logically scoped change at a time.
4. Add or update fixtures when observable language behavior changes.
5. Run the repository validator.
6. Open a pull request explaining the behavior before and after the change.

```bash
python3 scripts/validate_repository.py
```

The validator checks `VERSION`, current-version references, every fixture's
JSON structure, and local Markdown links. CI runs the same command.

## Normative writing

- Use **MUST**, **MUST NOT**, **SHOULD**, and **MAY** deliberately.
- State observable behavior independently of a host language or data type.
- Put implementation details in informative notes, not normative rules.
- Keep one rule in one authoritative place and cross-link to it elsewhere.
- Mark unresolved choices explicitly instead of guessing.
- Ground new rules in verified implementation behavior when possible, while
  remembering that this repository remains the language authority.

## Conformance fixtures

Read [conformance/README.md](./conformance/README.md) before adding a fixture.
Fixtures must be deterministic, implementation-independent, and minimal. A
fixture belongs under the directory matching the language version it tests.
Do not encode host-language limitations into an expected result.

When changing behavior, include a fixture that fails under the old behavior
and passes under the proposed rule. Security-sensitive rules should include a
negative fixture where the fixture schema can represent one.

## Language version changes

`VERSION` contains the current language version. Clarifications that do not
change observable behavior normally do not require a bump. A significant or
breaking language change must advance the draft version by one appropriate
SemVer step and must also:

- create or rename the matching `conformance/v<version>/` directory;
- update version references in the normative documents;
- add a matching entry to `CHANGELOG.md`; and
- identify implementation migration work in the pull request.

Implementation package versions are independent from the language version.

## Commit and review expectations

Use clear imperative commit messages and keep commits narrowly focused.
Reviewers will look for consistency across specification sections, fixture
coverage, compatibility impact, implementability outside Rust and
JavaScript, and sandbox implications.

Be kind and technical. Critique the proposal, not the person.

---

**Legal notice.** These contribution instructions are initial project terms.
They have not been reviewed by a lawyer.
