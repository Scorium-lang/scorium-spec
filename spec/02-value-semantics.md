# 2. Value semantics

**Status: first full draft, language version `0.1.0-draft`. Normative.
Derived from `scorium-rust`'s `Value` type and evaluator
(`crates/scorium-core/src/value.rs`, `crates/scorium-lua/src/eval.rs`).**

## Value types

```
Value ::= Int(i64-range integer)
        | Float(IEEE-754 double)
        | Bool(true | false)
        | Nil
        | Str(string)
        | Color(r: u8, g: u8, b: u8, a: u8)
        | Duration(amount: f64, unit: ms | s | m)
        | List(Value*)
```

Eight value types, no others, for `0.1.0-draft`. An implementation MUST
keep `Int` and `Float` distinct representations — collapsing both into one
numeric type (as a prototype implementation might, for convenience) is a
non-conformant simplification, because it silently changes arithmetic and
formatting results (see below).

`Color` is stored as four real channels, not a string — `primary.darken(0.25)`
operates on the channels directly. `Duration` stores `(amount, unit)`, not a
normalized millisecond count — the unit is part of the value's identity, not
just display formatting.

## Truthiness

Lua-style: every value is truthy except `Nil` and `Bool(false)`. In
particular `0`, `0.0`, `""`, and `[]` (empty list) are all truthy. This
MUST NOT be reimplemented as C-style falsy-zero.

## Arithmetic (`+ - * / %`)

- `Int op Int` stays `Int` for `+`, `-`, `*`, using **checked** arithmetic:
  overflow MUST raise `scorium::eval::arithmetic_overflow` (see §5), never
  silently wrap or promote to a bigger/float type.
- `Int / Int` MUST always produce a `Float`, even when evenly divisible
  (`6 / 2` is `Float(3.0)`, not `Int(3)`). This is a deliberate asymmetry
  with `+`/`-`/`*` and MUST be preserved — it's the one operator where
  Scorium's integer type does not stay closed under itself.
- `Int % Int` MUST use Euclidean remainder, defined mathematically (not by
  reference to any host language's `%`) so every implementation agrees
  independent of what their native operator happens to do:

  ```
  a % b = r  such that  a = b*q + r  for some integer q,  and  0 <= r < |b|
  ```

  This is well-defined for any `b != 0` and both operand signs. Worked
  examples (this table is itself a conformance-fixture candidate):

  ```
   5 %  3 = 2
  -5 %  3 = 1
   5 % -3 = 2
  -5 % -3 = 1
  ```

  Note the result's sign always matches this `0 <= r < |b|` rule, not the
  sign of either operand — this deliberately differs from Rust's/C's
  truncated `%` and from what some languages' native operator gives for
  negative operands; implementations MUST NOT delegate to their host
  language's built-in `%` without checking it actually implements
  Euclidean semantics. `i64::MIN % -1` is defined as `0` (the mathematical
  result; naively computing it via a native truncating `%`/`rem` would
  overflow).
- Division or modulo by an integer/float zero MUST raise
  `scorium::eval::division_by_zero`.
- Any arithmetic op where at least one operand is a `Float` (and the other
  is `Int` or `Float`) produces a `Float`, computed as an ordinary IEEE-754
  double operation — no overflow checking (floats saturate to infinity per
  IEEE-754, which is accepted, not an error).
- Arithmetic on any other value type (or type pair) MUST raise
  `scorium::eval::type_error`, naming both operand types.
- Unary `-` on `Int` uses checked negation (overflow error on
  `Int::MIN`); unary `-` on `Float` is ordinary negation.

## Comparison (`< > <= >= == ~=`)

- `Int`/`Int`, `Float`/`Float`, `Str`/`Str` compare natively.
- `Int`/`Float` (either order) MUST compare using **exact** semantics, not
  by casting the integer to a float first: casting can lose precision for
  integers beyond `2^53`, causing values that are actually different to
  compare equal. This MUST NOT be implemented as `(n as f64) == f` (or the
  ordered equivalent) for an arbitrary `i64` — the algorithm, in order:

  1. If the float is `NaN`, the comparison result is defined by the NaN
     rule below (never proceed past this step).
  2. If the float is `+Infinity` or `-Infinity`, the comparison is
     trivial: every finite integer is less than `+Infinity` and greater
     than `-Infinity`.
  3. If the float's magnitude falls entirely outside the representable
     `i64` range (below `i64::MIN` or `>= i64::MAX + 1` as an `f64`), the
     comparison is trivial by range: the integer is greater/less than the
     float accordingly, without converting the float further.
  4. Otherwise, the float is within (or at the edge of) `i64` range and
     finite: truncate its integer part and convert *that bounded value*
     to `i64` (safe, since step 3 already excluded out-of-range floats),
     then compare the two integer parts exactly.
     - If the integer parts differ, that ordering is the answer.
     - If they're equal, break the tie using the float's fractional part:
       a positive fractional remainder makes the float greater than the
       integer; a negative one makes it less; a zero remainder makes them
       equal.

  See `scorium-rust`'s `cmp_int_float` for a reference implementation of
  steps 3–4 (its range checks and step 2's infinity handling collapse
  into the same bounds test, since `±Infinity` already falls outside the
  `i64`-representable range).
- Any comparison against `NaN` (ordered `< > <= >=`) MUST evaluate to
  `false`, matching Lua's NaN behavior — not raise an error. This applies
  whether the `NaN` came from a `Float`/`Float` or `Int`/`Float` pair.
- **Equality** between `Int(n)` and `Float(f)` MUST use this precise
  definition, not a looser "close enough" or naive-cast check:

  ```
  Int(n) == Float(f)   iff   f is finite
                         AND  f has no fractional component
                         AND  f falls within the exactly-convertible i64 range
                         AND  (f truncated and converted to i64) == n
  ```

  Every clause must hold — a finite float with a fractional part, or one
  outside exact range, is never equal to any integer regardless of
  rounding. `==`/`~=` between any other mismatched types (e.g. `Str` vs
  `Int`) is `false`/`true` respectively, not an error.
- Ordered comparison (`< > <= >=`) between incompatible types (e.g. `Bool`
  vs `Int`, or either against `Color`/`Duration`/`List`/`Nil`) MUST raise
  `scorium::eval::type_error`.

## Color methods

`darken(amount)`, `lighten(amount)`, `alpha(amount)` are the only color
operations, each taking one numeric argument (`Int` or `Float`, coerced to
`f64`) clamped to `0.0..=1.0`:

- `darken`: each RGB channel scaled by `1 - amount`, alpha unchanged.
- `lighten`: each RGB channel linearly mixed toward `255` (white) by
  `amount`, alpha unchanged.
- `alpha`: replaces the alpha channel with `round(amount * 255)`.

All channel math rounds to the nearest `u8` (round-half-away-from-zero, per
Rust's `f64::round`); implementations in languages with different default
rounding (e.g. banker's rounding) MUST explicitly match round-half-away,
not their language default.

Calling any other method name on a color, or calling a color method with
the wrong argument count/type, MUST raise `scorium::eval::type_error`.
No other value type has methods in `0.1.0-draft`.

## Duration semantics

A duration is `(amount: f64, unit)`. There is no implicit conversion
between units at the value level — `as_millis()`-style normalization (for
comparison or host consumption) is a host/runtime convenience, not
something the language does implicitly to two durations with different
units in an expression. (Whether durations of different units can be
compared/added at all in `0.1.0-draft` is unresolved — `scorium-rust`'s
current evaluator does not appear to define duration arithmetic; treat
duration values as opaque outside of construction and host consumption
until this is confirmed against the reference implementation and stated
here explicitly.)

## Lists

`List(Value*)` — no declared element-type constraint at the value level;
mixed-type lists are permitted by the value model (schema-level
homogeneity constraints, if any, are `scorium-schema`'s concern, not a
core value-semantics rule).

## Numeric range and exact representation

`Int` is specified as the full signed 64-bit range (`i64`) to match
`scorium-rust`. This is a language contract, stated as an outcome, not a
representation:

**Every conforming implementation MUST represent the complete Scorium
`Int` domain — the full 64-bit signed integer range — exactly, with no
precision loss for any representable value.** The exact-comparison and
exact-equality rules above assume a true integer domain; an
implementation whose internal `Int` representation loses precision
anywhere in that range does not satisfy them, regardless of how it gets
there internally.

How a given host language's implementation satisfies this is that
implementation's own concern, not this document's — this spec fixes the
contract, not the representation technology. (For example: a language
whose native numeric type does not cover the full `i64` range exactly
would need some wider-than-native integer representation to conform; the
specific choice and its trade-offs belong in that implementation's own
docs, e.g. a future `scorium-js` implementation note — not here.) Adding
implementation-technology prescriptions to this document is exactly the
kind of repo-proximity coupling `scorium-spec` exists to avoid (see
`README.md`).

## Open questions

- Duration arithmetic/comparison across units (see above) needs
  confirmation against `scorium-rust` behavior, not assumption.
