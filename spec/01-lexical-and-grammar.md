# 1. Lexical structure and grammar

**Status: first full draft, language version `0.1.0-draft`. Normative for
implementations targeting this version. Derived from `scorium-rust`'s
parser (`crates/scorium-core/src/{lexer,parser}.rs`, documented in
`scorium-rust/docs/GRAMMAR.md`) as initial ground truth — not yet
cross-checked against a second implementation, so treat as draft until
`scorium-go` has attempted to conform to it.**

Notation is extended-BNF-ish, written for readability over formality.
`{ x }` means zero or more; `[ x ]` means optional; alternatives are
separated by `|`.

Every implementation MUST accept and reject input identically per this
grammar for language version `0.1.0-draft`. Where behavior described here
turns out to diverge from what `scorium-rust` actually does, that is a bug
to fix explicitly (in the spec or in `scorium-rust`), not something a new
implementation should silently match by copying Rust's behavior without
recording the discrepancy.

---

## Lexical structure

### Whitespace and newlines

Whitespace (space, tab) and newlines separate tokens. Scorium is
newline-sensitive at the statement level: a leaf, node, variable
definition, or statement begins on a new line (or after `{`, `then`, `do`,
`else`, `elseif`).

### Comments

```
comment      ::= line_comment | block_comment
line_comment ::= '#' rest_of_line
              |  '--' rest_of_line
block_comment::= '--[[' ... ']]'
```

`#` is also the color-literal prefix, but only where a **value** is
expected (after `=`, inside a list, as a function argument). A `#` starting
a token where a statement or value is not expected begins a line comment.

Block comments do not nest (nesting is explicitly out of scope for
`0.1.0-draft` — see Roadmap alignment below).

### Identifiers and markers

```
ident      ::= ident_start { ident_continue }
ident_start::= letter | '_'
ident_continue ::= letter | digit | '_' | '-'
vardef     ::= '@' ident          # only on a definition line
interp     ::= '$' ident          # only inside a bare string
```

Identifiers may contain `-`, so `node-1`, `SUPER+Return`-style tokens and
dotted bare strings (`cert.pem`) lex as single bare-string tokens in the
right context.

### Literals

```
int        ::= digit { digit }
float      ::= digit { digit } '.' digit { digit }
              |  '.' digit { digit }
bool       ::= 'true' | 'false'
nil        ::= 'nil'
color      ::= '#' hex6 | '#' hex8
hex6       ::= hex hex hex hex hex hex
hex8       ::= hex6 hex hex
duration   ::= number unit
unit       ::= 'ms' | 's' | 'm'
number     ::= int | float
quoted_str ::= '"' { char_or_escape } '"'
```

A duration without a unit is **not** a duration — it is an integer or
float. Whether a unitless number is accepted where a duration is expected
is a schema-level decision (rejected by default; see §2 Value semantics).

The `int` vs. `float` distinction here is normative and cross-language:
implementations MUST NOT collapse both into a single numeric
representation (see §2 for the coercion rules this implies).

### Operators

```
add_op   ::= '+' | '-'
mul_op   ::= '*' | '/' | '%'
rel_op   ::= '<' | '>' | '<=' | '>=' | '==' | '~='
logic_op ::= 'and' | 'or'
unary_op ::= '-' | 'not'
```

Binary operators require spaces on **both sides** inside an expression.
`base*2` MUST be rejected by the lexer as a squeezed operator, with a
diagnostic suggesting `base * 2`. This is deliberate: it stops `base*2`
from being silently read as a bare string.

---

## Syntax

### Document and items

```
document   ::= { item } { comment }

item       ::= leaf
             | node
             | vardef_stmt
             | include
             | if_stmt
             | for_stmt
             | while_stmt
             | local_stmt
             | return_stmt
             | fn_def
             | script_block
             | call_stmt
```

### Leaves and nodes

```
leaf       ::= ident '=' expr
node       ::= ident [ header ] '{' newline { item } '}'
header     ::= bare_value | quoted_str
```

A node header is a single bare token or quoted string. Its semantics are
host-defined, not language-defined.

### Variables and locals

```
vardef_stmt::= vardef '=' expr          # `@name = expr`
local_stmt ::= 'local' ident '=' expr
```

`@name` defines a variable visible to later items in the same or enclosing
scope. `local name = expr` introduces a lexically scoped variable (used for
loop counters and function bodies). A `key = value` leaf whose key is
already a `local` reassigns that local in place — this is the only
spelling Scorium has for updating a counter (see "Reassignment" below).

### Control flow

```
if_stmt    ::= 'if' expr 'then' newline { item }
               { 'elseif' expr 'then' newline { item } }
               [ 'else' newline { item } ]
               'end'
for_stmt   ::= 'for' ident '=' expr ',' expr [ ',' expr ] 'do' newline { item } 'end'
while_stmt ::= 'while' expr 'do' newline { item } 'end'
return_stmt::= 'return' [ expr ]
```

The numeric `for` is inclusive on both ends (`for i = 1, 3` runs for `i` in
`1, 2, 3`). The optional third expression is the step; the default step is
`1`; a step of `0` MUST be a type error.

### Functions and scripts

```
fn_def     ::= 'fn' ident '(' [ ident { ',' ident } ] ')' '{' newline { item } '}'
script_block ::= 'script' '{' raw_lua_text '}'
call_stmt  ::= expr_call                # a call used as a statement
```

A `fn` body is ordinary Scorium items, not Lua. `return` exits the function
and may carry a value. A `script { }` body is raw Lua text handed verbatim
to a sandboxed Lua runtime — it MUST NOT be transpiled or reformatted.
`script { }` is scoped separately in §7 (conformance levels): an
implementation that does not embed Lua is not required to execute this
production, but MUST still parse and recognize it in order to emit the
correct diagnostic per §5, rather than failing generically or silently
skipping it.

### Includes

```
include    ::= 'include' string_literal
```

The path is a quoted string or a bare string literal. Resolution, cycle
detection, and traversal policy are evaluation/sandbox behavior (§3, §6),
not grammar.

---

## Expressions

```
expr       ::= or_expr
or_expr    ::= and_expr { 'or' and_expr }
and_expr   ::= cmp_expr { 'and' cmp_expr }
cmp_expr   ::= add_expr [ rel_op add_expr ]
add_expr   ::= mul_expr { add_op mul_expr }
mul_expr   ::= unary { mul_op unary }
unary      ::= unary_op postfix | postfix
postfix    ::= primary { call_suffix | member_suffix }
call_suffix::= '(' [ expr { ',' expr } ] ')'
member_suffix ::= '.' ident
primary    ::= int | float | bool | 'nil' | color | duration
             | quoted_str | bare_str | list | '(' expr ')' | ident
list       ::= '[' [ expr { ',' expr } ] ']'
```

### Strings

```
quoted_str ::= '"' { char | escape } '"'        # literal, no interpolation
bare_str   ::= { bare_text | interp }           # interpolation allowed
escape     ::= '\' ('"' | '\' | 'n' | 't' | 'r')
```

`$name` interpolation is allowed **only** inside a bare string. Inside a
quoted string, `$name` is literal text. Escapes beyond `\" \\ \n \t \r`
(e.g. `\u{...}`) are out of scope for `0.1.0-draft`.

### Identifier resolution

A bare `ident` used where an expression is expected MUST resolve at
evaluation time, in this exact priority order:

1. a lexical local / loop variable / function parameter;
2. an `@`-defined variable;
3. a sibling leaf emitted earlier in the same node body;
4. a host-registered value;
5. otherwise, the identifier **falls back to a literal string**.

This fallback-to-literal-string rule is load-bearing and easy to get
subtly wrong in a reimplementation: it is what lets `select(kitty,
alacritty, foot)` skip quoting. Every native implementation MUST replicate
this exact resolution order — a different order (e.g. checking
host-registered values before sibling leaves) is an observable, testable
divergence, not an internal detail.

A `$name` in a bare string has no fallback: if undefined, it MUST be an
undefined-interpolation error, never a literal `$name`.

### Reassignment

Scorium has no separate assignment statement. A `key = value` leaf whose
key names an existing `local` updates that local instead of emitting a
leaf entry. This is required so a `while` loop can advance its own
counter:

```scor
local i = 0
while i < 3 do
    i = i + 1
end
```

`@`-defined variables are **not** reassignable through this mechanism —
only `local`s are. An implementation that allowed reassigning an
`@`-variable this way would silently diverge from every other
implementation's scoping behavior.

---

## Reserved words

The following are reserved and MUST NOT be used as a bare node name or
identifier-as-value in the obvious way:

```
if  then  elseif  else  end
for  do  while
fn  local  return  nil  true  false
and  or  not
include  script
```

Using one as a node name MUST produce a `reserved_word` diagnostic (code
namespace defined in §5).

---

## Roadmap alignment for `0.1.0-draft`

Explicitly out of scope for this spec version (tracked as future spec
versions once there is a concrete need, not implied by their absence
here):

- Host-pluggable literal *syntax* (new lexer-level token shapes registered
  by a host, e.g. a bespoke `10MB` byte-size token). The host-defined
  *type* extension point (validating an already-parsed value) is a
  runtime/schema concern, not a grammar concern, and is unaffected.
- Generic `for` over tables/iterators — only the numeric `for` is
  specified. (A Lua-capable implementation's `script { }` body may still
  use Lua's own generic `for`; that is Lua's grammar, not Scorium's.)
- A `.scor`-based schema file format.
- String escapes beyond `\" \\ \n \t \r`.
- Block-comment nesting and comment tracking inside expressions/lists.

## Open questions

- Whether this spec fixes a concrete lexer error-recovery model, or only
  successful-parse behavior (error message *text* is diagnostics' concern
  per §5, but error *sites* — where parsing must fail — are grammar's, and
  are not yet exhaustively enumerated here).
- This draft has not yet been checked against a second parser
  implementation; until `scorium-go` attempts conformance, treat every
  production above as "believed correct," not "proven portable."
