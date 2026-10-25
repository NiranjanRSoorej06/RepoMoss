# RepoMoss

RepoMoss is a local-first maintenance assistant. It scans a selected Git repository for a small set of concrete issues, ranks evidence-backed findings, and can make one deterministic documentation repair in an isolated Git worktree. It never merges or edits the original checkout.

## Run locally

Requirements: Python 3.11+, Git, and (optional) Ollama. Install the backend and start the loopback-only web app:

```sh
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m app
```

Open <http://127.0.0.1:8000>. In the UI, register a local Git repository and scan it. Findings can be approved, deferred, or rejected. Ollama is optional; set `OLLAMA_MODEL` and `OLLAMA_URL` to enable local task explanations. RepoMoss sends only the finding evidence to Ollama; it never sends repository data to a hosted inference API.

## Verification commands

Verification is opt-in and commands must be configured by the operator. Set one exact command per line in `REPOMOSS_VERIFY_COMMANDS` before starting the server, for example:

```sh
export REPOMOSS_VERIFY_COMMANDS='python -m pytest'
```

The UI accepts only commands that exactly match this list. Each command has a 120 second timeout, output is capped at 50 KB, and logs are stored under `~/.repomoss/logs`. Keep allowlisted commands appropriate for the selected repository: a command may execute repository code. No commands are run by default.

## What works in this MVP

- Repository validation, branch/commit and dirty-state capture.
- Bounded scanner for TODO/FIXME/XXX markers in Markdown and broken relative Markdown links.
- Deterministic finding priorities and SQLite task/scan/run history.
- Optional Ollama explanation with schema and file-scope checks plus deterministic fallback.
- Explicit task approval and defer/reject controls.
- Isolated worktree execution for one narrow fix: convert a broken local Markdown link to its visible plain-text label.
- Exact allowlist verification, bounded logs, diff and Markdown report endpoints.

TODO findings are surfaced for review but are not automatically patched. The model only explains findings; it cannot issue shell commands or supply patches in this MVP. Verification output is evidence, not proof of correctness. Cancellation, scheduled execution, broad code patching, auto-merge, and OS-level sandboxing are not implemented.

## Data and security

The database, retained worktrees, diffs and logs live under `~/.repomoss` (override the database path with `REPOMOSS_DB`). The service binds to `127.0.0.1`; do not expose it to a network. The scanner skips common dependency/build directories, symlinks, likely secrets and files larger than 1 MB, and stops after 10,000 files. Git worktrees isolate changes from your checkout, but they are not a security sandbox. Treat untrusted repositories and verification commands accordingly.

See [Safety](docs/SAFETY.md) and [Architecture](docs/ARCHITECTURE.md) for details.
