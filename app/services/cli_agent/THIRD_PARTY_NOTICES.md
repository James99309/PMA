# Third-Party Notices

This module (`app/services/cli_agent/`) contains Python code whose **design patterns, algorithms, and architectural strategies** are adapted from the following third-party open source projects. All Python code in this directory is an original implementation; no source code from the referenced projects is reproduced verbatim.

## ultraworkers/claw-code

- **Repository**: https://github.com/ultraworkers/claw-code
- **License**: MIT License
- **Language**: Rust
- **Usage in this module**: Design concepts only (no line-by-line translation)

### Patterns adapted

| Our Python file | claw-code Rust source | What was adapted |
|---|---|---|
| `conversation.py` | `rust/crates/runtime/src/conversation.rs` | ContentBlock enum shape (Text / ToolUse / ToolResult), tool_use_id pairing semantics, per-message usage tracking |
| `compaction.py` | `rust/crates/runtime/src/compact.rs` + `summary_compression.rs` | Rule-based (non-LLM) summarization approach, "preserve recent N + compress older" split strategy, stackable summary layering |
| `prompt_builder.py` | `rust/crates/runtime/src/prompt.rs` | Static/dynamic section boundary pattern for prompt-cache-friendly assembly |
| `usage.py` | `rust/crates/runtime/src/usage.rs` | Per-turn usage block structure, cumulative tracking shape |
| `llm_client.py` | `rust/crates/api/src/client.rs` (partial) | Request hashing concept for cache effectiveness detection (Python implementation uses explicit `cache_control` instead) |

### MIT License Notice (claw-code)

```
MIT License

Copyright (c) UltraWorkers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Anthropic Python SDK (`anthropic`)

- **Package**: https://github.com/anthropics/anthropic-sdk-python
- **License**: MIT License
- **Usage**: Direct dependency (declared in requirements), not source-copied

Used for:
- LLM client (`messages.create` / `messages.stream`)
- Native tool use protocol
- Prompt caching via `cache_control`
- `count_tokens` API for accurate token estimation

## xterm.js (frontend only)

- **Repository**: https://github.com/xtermjs/xterm.js
- **License**: MIT License
- **Usage**: Frontend dependency loaded in `app/templates/cli/terminal.html`, not source-copied
