# Git & board rules (always apply)

- Never commit or push directly to `main`. One branch per ticket:
  `feat/<issue>-<slug>`. Pipeline changes go on `chore/<topic>`.
- Small commits with prefixes: `test:`, `feat:`, `refactor:`, `docs:`, `chore:`,
  and the issue number: `feat: add goal list view (#3)`.
- Never merge a PR, force-push or rewrite pushed history without explicit
  tech-lead instruction.
- Never move an issue to **Ready** or **Done** on your own. Ready = tech-lead
  approval; Done happens only through `finish-ticket` after the merge.
- Never add a dependency (`uv add`) that isn't in the approved plan.
- Never bypass git hooks (`commit -n` / its long form); fix what they report.
