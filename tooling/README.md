# Scorium tooling contract v1

This directory defines stable cross-implementation behavior for tools. It is
versioned independently from implementation package versions and is additive:
new optional fields may appear, but existing field meanings do not change
within v1.

## Commands and exit status

All command-line implementations provide `check`, `parse`, `fmt`, and `eval`.

- `0` means the command succeeded.
- `1` means the input, evaluation, schema, formatting check, or I/O operation
  failed.
- `2` means command-line usage was invalid.

`check --json`, `parse --json`, and `eval --json` write exactly one JSON value
to standard output. Human diagnostics never share standard output in JSON
mode.

## `check --json`

The result object contains:

- `ok`: whether checking succeeded;
- `language_version`: the implemented Scorium language revision;
- `source`: the source name supplied to the command;
- `entries`: evaluated top-level entry count, present on success;
- `diagnostics`: diagnostics in deterministic order.

Each diagnostic has `code`, `stage`, `severity`, `message`, `source`, `range`,
and `related`. `source` identifies the file where the problem originated,
including an included file. Codes are the stable contract; message text is informative. Ranges
are half-open, zero-based LSP positions. `character` counts UTF-16 code units.
An error without a meaningful source location uses the zero-width range at
line 0, character 0. `related` is an array reserved for secondary locations.

## `parse --json`

The root is:

```json
{
  "type": "document",
  "language_version": "0.2.1",
  "items": []
}
```

Items use a `kind` discriminator. The v1 item kinds are `leaf`, `node`, `var`,
`include`, `if`, `for`, `while`, `local`, `return`, `function`, `call`, and
`script`. Expressions likewise use `kind`: `int`, `float`, `bool`, `nil`,
`string`, `color`, `duration`, `list`, `identifier`, `unary`, `binary`,
`member`, and `invoke`.

Integer and floating-point payloads are strings so host JSON number limits do
not alter the tree. The non-finite float spellings are `nan`, `inf`, and
`-inf`. The syntax tree retains quoted-versus-bare strings, interpolation
parts, and quoted-versus-bare node headers. It deliberately omits source
spans, comments, and formatter trivia; those remain available through each
implementation's native AST.

## Capabilities

The tooling behavior is shared across ports. Runtime capabilities may differ:
Rust executes `script {}` through its sandboxed Lua runtime; JavaScript and Go
intentionally report `scorium::eval::script_error`. A missing capability is an
explicit diagnostic, never silent success.
