# Safety boundaries

- The server binds to loopback. Keep it local; there is no authentication layer.
- A repository must be registered before scanning. Paths are resolved and Git metadata is captured.
- Scanning does not follow symlinks, skips common generated/dependency directories and likely secret files, limits individual files to 1 MB and total entries to 10,000.
- Worktree attempts require a clean original checkout and an unchanged base commit. The generated branch is retained for review.
- Only explicitly approved findings can be attempted. Only the deterministic broken-Markdown-link repair is implemented.
- Model output is explanatory and validated; no model-supplied path outside the finding scope is accepted and model output is never executed.
- Verification is disabled by default. The operator configures exact commands; there is a 120 second timeout and output is limited to the last 50 KB.
- A Git worktree is not a sandbox. Allowlisted commands can execute repository code with the server user's permissions. For untrusted code use a separate OS account/container with restricted filesystem and network access.
- Failed/blocked attempts are recorded and the worktree is retained. RepoMoss never merges, pushes, or copies changes into the original checkout.
