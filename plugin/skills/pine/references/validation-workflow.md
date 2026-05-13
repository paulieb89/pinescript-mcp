# validate_function — workflow reference

The `validate_function` MCP tool is the gate that prevents hallucinated function names from reaching the user. This reference defines the exact call pattern and how to act on responses.

## Tool signature

Tool name: `validate_function`

Input:

| Parameter | Type | Description |
|-----------|------|-------------|
| `fn_name` | string | Function name to validate. Bare name only — no parentheses, no arguments. E.g. `"ta.rsi"`, `"strategy.entry"`, `"plot"`. |

Output: `ValidationResult`, a Pydantic model with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `valid` | bool | `true` if the function is in the Pine v6 allowlist. |
| `type` | `"namespaced"` \| `"toplevel"` \| `null` | Function category when valid; `null` when invalid. |
| `function` | string | Echo of the input name. |
| `suggestion` | string \| null | When `valid: false`, a recommended replacement or remediation hint. `null` when valid. |

## Decision logic

```
For each unique function name in the draft:
    result = validate_function(fn_name)
    if result.valid is true:
        proceed.
    else:
        read result.suggestion.
        if suggestion names a specific replacement function:
            use the replacement.
            fetch the replacement's doc section via get_section or resolve_topic.
            re-validate the replacement (it must also pass validate_function).
        else:
            the suggestion will point to get_functions(namespace) — call it,
            pick the correct function from the listed valid options,
            then validate that choice.
```

## What to extract from the draft

Match every token that looks like a function call. Two patterns:

1. **Namespaced:** `<word>.<word>(` — e.g. `ta.rsi(`, `request.security(`, `strategy.entry(`, `array.push(`, `math.max(`.
2. **Top-level:** a bare `<word>(` at a function-call position — e.g. `plot(`, `indicator(`, `strategy(`, `nz(`, `na(`, `bool(`, `int(`, `input.int(`.

Strip the trailing `(` and any arguments. Validate the **bare name only**.

Deduplicate before calling — if `ta.rsi` appears three times, validate once.

Do **not** skip "obvious" functions. `plot`, `indicator`, `input.int`, `request.security` all go through validation. The tool is fast and cached server-side.

## Worked example: `ta.adx` → `ta.dmi`

Suppose the draft contains:

```pine
adxVal = ta.adx(14)
```

Step-by-step:

1. Call `validate_function(fn_name="ta.adx")`.

2. Receive:

   ```json
   {
     "valid": false,
     "type": null,
     "function": "ta.adx",
     "suggestion": "ta.adx() does NOT exist. Use ta.dmi(diLen, adxSmoothing) → returns [diPlus, diMinus, adx] as a tuple."
   }
   ```

3. The suggestion names a specific replacement: `ta.dmi`. Note that it returns a **tuple** of three values, not a single scalar — the calling code must be rewritten to destructure.

4. Fetch the docs for `ta.dmi` to confirm the parameter order and return shape:

   - Call `resolve_topic(query="ta.dmi")`, or
   - Call `get_section(path="reference/functions/ta.md", header="ta.dmi")`.

5. Re-validate: `validate_function(fn_name="ta.dmi")`.

6. Receive:

   ```json
   {
     "valid": true,
     "type": "namespaced",
     "function": "ta.dmi",
     "suggestion": null
   }
   ```

7. Rewrite the draft:

   ```pine
   [diPlus, diMinus, adxVal] = ta.dmi(14, 14)
   ```

8. Proceed to emit.

## Worked example: `security` → `request.security`

1. `validate_function(fn_name="security")` returns:

   ```json
   {
     "valid": false,
     "type": null,
     "function": "security",
     "suggestion": "security() was renamed in v5. Use request.security() instead."
   }
   ```

2. Substitute `request.security` everywhere in the draft.

3. Re-validate: `validate_function(fn_name="request.security")` → `valid: true`.

4. Confirm parameter shape via `resolve_topic(query="request.security")` and adjust call sites if needed (the v6 signature uses named args for `lookahead`, `gaps`, etc.).

## Worked example: unknown function with namespace hint

If a function is invalid but no specific replacement is known, the suggestion points you at `get_functions`:

```json
{
  "valid": false,
  "type": null,
  "function": "ta.foo",
  "suggestion": "Not found in ta.*. Use get_functions('ta') to see all valid ta.* functions."
}
```

Action: call `get_functions(namespace="ta")`, pick the correct function for the intended purpose, then validate that choice.

## Failure modes — do not silently fall back

If `validate_function` itself errors (network failure, MCP server unreachable):

- Do **not** emit unvalidated code.
- Tell the user the MCP server is unreachable and the validation gate cannot run.
- Suggest they check the MCP connection or run the server locally via `uvx pinescript-mcp`.

## Validation budget

A typical small indicator uses 5–10 distinct functions. A complex strategy uses 15–25. Validation is cheap — server-side cache TTL is roughly five minutes. Validate every function. Do not optimise away the gate.
