# Project rules

1. **No emojis.** Never use emojis anywhere - code, comments, docs, commit messages, PR descriptions, chat output.
2. **No Claude Code attribution.** Do not add `Co-Authored-By: Claude ...`, "Generated with Claude Code", or any similar attribution to commits, PRs, or files.
3. **Conventional Commits** for all git activity - commit messages, branch names, and PR titles.
   - Format: `<type>(<scope>)?: <description>` (e.g. `feat(scripts): port BYM predict from Kigali source`, `fix(dockerfile): pin BASE_PLATFORM=linux/amd64`).
   - Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `perf`, `style`, `revert`.
   - Branch names: `<type>/<short-description>` (e.g. `feat/initial-port`, `fix/predict-year-derive`).
