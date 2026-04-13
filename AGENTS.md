# Code Review Rules

## General
- Keep changes minimal and focused.
- Prefer shared utilities over duplicated logic.
- Preserve existing project structure and conventions.
- Update translations when UI labels change.

## Python
- Follow existing style and naming conventions.
- Avoid unnecessary comments.
- Reuse shared filters and state helpers for UI status logic.

## Qt UI
- Keep labels localized through `locales/*.json`.
- Prefer consistent status semantics across Home and Recordings views.
