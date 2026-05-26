# Yield Shell MCP

A drop-in shell MCP that auto-yields long-running commands into managed background processes.

## Why Auto-Yielding?

Most shell tools force a choice: block the agent until the command finishes, or require the agent to decide up front that a command should be backgrounded. Yield Shell MCP keeps normal foreground semantics for fast commands, then automatically promotes long-running commands into managed background processes after `yield_ms` (default 1 second). The agent gets output immediately for quick tasks and a stable `process_id` for follow-up on slow ones.

## Install

Published package:

```bash
uv tool install mcp-yield-shell
```

Local development:

```bash
git clone <repo-url> && cd mcp-yield-shell
uv sync
uv run mcp-yield-shell
```

## MCP Client Configuration

### OpenCode

Add to your OpenCode MCP config:

```json
{
  "mcpServers": {
    "yield-shell": {
      "command": "uvx",
      "args": ["mcp-yield-shell"]
    }
  }
}
```

### Generic MCP stdio

```json
{
  "mcpServers": {
    "yield-shell": {
      "command": "uvx",
      "args": ["mcp-yield-shell"]
    }
  }
}
```

For local development, replace `uvx` with `uv run` and set the working directory.

## Usage Examples

### Fast command (completes within yield_ms)

```json
{"tool": "exec", "input": {"command": "echo hello"}}
```

Response:

```json
{
  "status": "completed",
  "exit_code": 0,
  "duration_ms": 45.2,
  "stdout": "hello\n",
  "stderr": "",
  "truncated": false
}
```

### Long command (backgrounded after yield_ms)

```json
{"tool": "exec", "input": {"command": "sleep 60"}}
```

To immediately background a process without waiting, set `yield_ms` to 0:

```json
{"tool": "exec", "input": {"command": "sleep 60", "yield_ms": 0}}
```

Response:

```json
{
  "status": "backgrounded",
  "process_id": "proc_a1b2c3d4e5f6",
  "pid": 12345,
  "duration_ms": 1002.3,
  "stdout": "",
  "stderr": "",
  "truncated": false,
  "message": "Process is running in the background. Use read/wait/stop with process_id."
}
```

### Follow-up read (incremental)

Each `read` or `wait` response includes a `next_seq` integer. Pass it as `since_seq` on the next call to fetch only new output since the last read. When `since_seq` is omitted, all retained output is returned from the beginning of the buffer.

```json
{"tool": "read", "input": {"process_id": "proc_a1b2c3d4e5f6", "since_seq": 3}}
```

### Process list

```json
{"tool": "ps", "input": {"include_completed": false, "limit": 10}}
```

### Write to stdin

```json
{"tool": "write", "input": {"process_id": "proc_a1b2c3d4e5f6", "input": "hello", "newline": true}}
```

### Wait for a process

```json
{"tool": "wait", "input": {"process_id": "proc_a1b2c3d4e5f6"}}
```

`wait` returns when the process exits or the wait timeout expires. It does **not** kill the process on wait timeout.

### Stop a process

```json
{"tool": "stop", "input": {"process_id": "proc_a1b2c3d4e5f6"}}
```

## Tool Reference

| Tool | Key Inputs | Key Outputs |
|------|-----------|------------|
| `exec` | `command` (required), `cwd`, `env`, `stdin`, `name`, `yield_ms`, `timeout_ms`, `max_output_bytes`, `auto_background` | `status` (completed/backgrounded/failed_to_start/timed_out/stopped/failed), output, `process_id` if backgrounded or timed_out |
| `read` | `process_id`, `since_seq`, `max_output_bytes`, `streams` (stdout/stderr/both) | `process_id`, `status`, `exit_code`, `signal`, `stdout` and/or `stderr`, `next_seq`, `truncated` |
| `write` | `process_id`, `input`, `newline` | `process_id`, `ok`, `error` |
| `wait` | `process_id`, `timeout_ms`, `max_output_bytes` | `process_id`, `status`, `exit_code`, `signal`, `stdout`, `stderr`, `next_seq`, `truncated` — waits for exit but **does not kill** the process if the wait timeout expires |
| `stop` | `process_id`, `signal`, `force_after_ms` | `process_id`, `stopped`, `signal`, `error` |
| `ps` | `include_completed` (default true; when false, omits all non-running processes), `limit` | `processes` array; each entry has `process_id`, `pid`, `name`, `command`, `cwd`, `status`, `exit_code`, `signal`, `started_at`, `ended_at`, `duration_ms`, `stdout_bytes`, `stderr_bytes` |
| `cleanup` | `completed_older_than_ms`, `stopped_older_than_ms` | `removed` count — `stopped_older_than_ms` also removes `timed_out` and `failed` processes |

When `auto_background` is `false` (default `true`), `exec` waits until the command completes or `timeout_ms` expires instead of returning `backgrounded` after `yield_ms`.

### `exec` output variants

- **completed**: `status`, `exit_code`, `signal`, `duration_ms`, `stdout`, `stderr`, `truncated`
- **backgrounded**: `status`, `process_id`, `pid`, `duration_ms`, `stdout`, `stderr`, `truncated`, `message`
- **failed_to_start**: `status`, `error`
- **timed_out**: `status`, `process_id`, `exit_code`, `signal`, `duration_ms`, `stdout`, `stderr`, `truncated`
- **stopped**: `status`, `process_id`, `exit_code`, `signal`, `duration_ms`, `stdout`, `stderr`, `truncated`
- **failed**: `status`, `process_id`, `exit_code`, `signal`, `duration_ms`, `stdout`, `stderr`, `truncated`

### Process statuses

`running` → `completed` (natural exit) | `stopped` (agent-initiated stop) | `timed_out` (total timeout) | `failed` (internal error)

## Configuration

Set these environment variables before server startup:

| Variable | Default | Meaning |
|----------|---------|---------|
| `YIELD_SHELL_DEFAULT_CWD` | Current directory | Default working directory for commands |
| `YIELD_SHELL_ALLOWED_CWDS` | (none) | `os.pathsep`-separated roots; cwd must resolve under one when set |
| `YIELD_SHELL_MAX_OUTPUT_BYTES` | 20000 | Default and upper bound for retained/read output bytes |
| `YIELD_SHELL_MAX_PROCESSES` | 50 | Maximum managed processes before new starts are rejected |
| `YIELD_SHELL_DEFAULT_YIELD_MS` | 1000 | Default auto-yield delay |
| `YIELD_SHELL_MAX_YIELD_MS` | 30000 | Maximum accepted `yield_ms` |
| `YIELD_SHELL_DEFAULT_TIMEOUT_MS` | 0 | Default total runtime timeout (0 = none) |
| `YIELD_SHELL_DENY_COMMAND_REGEX` | (none) | Reject matching commands before execution |
| `YIELD_SHELL_ALLOW_COMMAND_REGEX` | (none) | If set, only allow matching commands |
| `YIELD_SHELL_REDACT_ENV_REGEX` | `TOKEN|KEY|SECRET|PASSWORD` | Secret env var name pattern; values are redacted from output |

The `env` tool parameter is an additive overlay: it merges with the parent environment, overriding matching keys and adding new ones, but never replaces the entire environment. Tool responses never expose raw environment variable values.

## Security Notes

- **Shell access is powerful.** This server runs arbitrary shell commands. Run it in a sandbox, container, or dedicated development workspace.
- **Redaction is best-effort.** Values of environment variables whose names match `YIELD_SHELL_REDACT_ENV_REGEX` are replaced in returned output, but this is not a security boundary. Secrets can still appear through command output, arguments, or indirect channels.
- **Command and cwd policy** help constrain the agent but are not a sandbox. A determined agent can bypass regex rules.
- **Platform signal limitations.** On POSIX, process groups are used for termination. On Windows, termination is best-effort and may not kill child processes.

## Development

```bash
uv sync                # Install dependencies
uv run pytest          # Run tests
uv run ruff check .    # Lint
uv run pyright         # Type check
uv build               # Build package
```

## License

MIT