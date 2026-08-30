# Changelog

## 0.2.0-draft — unreleased

All seven spec sections (`00`–`07`) are now first full drafts grounded
directly in `scorium-rs`'s source (not just its prose docs), each
flagging what's normative vs. still open. Highlights: `%` defined by
Euclidean-remainder formula independent of any host language's native
operator; `Int`/`Float` comparison and equality defined exactly (no
`(n as f64) == f`-style precision loss); numeric-range conformance stated
as an outcome (exact `i64` domain representation), not tied to any one
representation technology; canonical formatter output declared
byte-identical across implementations, not just idempotent per
implementation; `include` path containment required on the canonical
(symlink-resolved) path, not the textual one; resolved a real
`scorium-rs` inconsistency (`scorium::include::cycle` was dead code —
only `scorium::eval::include_cycle` is normative).

Added the conformance fixture encoding (tagged semantic values; a
dedicated `entries` shape for whole-document evaluation results, since a
plain JSON object can't represent repeated same-named nodes or headers;
source-to-source byte fixtures for the formatter) and a first batch of 31
fixtures across values/evaluation/diagnostics/formatter/sandbox, seeded
from `scorium-rs`'s own tests and examples and empirically verified
against a live build of `scorium-rs` — all 31 matched on the first run,
including one case (`formatter/float-whole-number-keeps-decimal`) not
covered by any existing `scorium-rs` test.

Prepared the specification as a standalone public repository with accurate
landing documentation, shared project terms, contribution and security
guidance, GitHub templates, and automated validation of version references,
fixtures, and local documentation links.

## 0.1.0-draft — unreleased

Initial skeleton. No normative content yet: section stubs only, seeded from
the current `scorium-rs` documentation (`docs/GRAMMAR.md`,
`docs/LANGUAGE.md`, `docs/DIAGNOSTICS.md`, `docs/ROADMAP.md`) as informative
source material, not as authoritative text.
