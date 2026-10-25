# Architecture

The MVP is a single local FastAPI process. `app.main` exposes repository, scan, task, run, diff, event and report APIs and serves the dashboard. `services.core` owns Git metadata, bounded scanning, Ollama planning, worktree operations, allowlisted verification and SQLite persistence. The frontend is a dependency-free browser dashboard calling the local JSON API.

SQLite stores repository, scan, finding, task, run, event and verification metadata. Logs and diffs are files under the local RepoMoss data directory. Ollama is optional and accessed on its local HTTP endpoint. The scanner is deterministic; model summaries do not affect the safety gate or execution commands.

Current workflow: register → scan → inspect evidence → approve → create worktree from recorded commit → apply the one supported link repair → run configured exact commands → inspect retained diff/report. Attempts never change the source checkout.
