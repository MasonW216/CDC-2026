# StormRoute — shared rules for Claude Code

Every Claude session and subagent in this repo inherits these rules.

## Sources of truth

- `docs/build_guide.md` is authoritative; `docs/project_specification.md` is the original spec. Where they disagree, the build guide wins (ADR 0000).
- Locked decisions live in `docs/adr/`. Changing one needs a new ADR the whole team approves.
- Acceptance criteria for each issue are in the GitHub issue (seeded from `docs/issue_backlog.md`). "Done" means every checkbox is ticked with evidence.

## Hard rules

- No production modeling, scoring, API, or website code lands before the Milestone 2 EDA gate (#6) is approved. Scaffold and data-download utilities are the exceptions (CONTRIBUTING.md).
- Never commit `data/raw`, `data/interim`, `data/processed`, `*.parquet`, `*.joblib`, secrets, or absolute local paths.
- Never change a canonical schema (build guide §6.3) or the repository structure (§4) without flagging it as a proposed change for all three teammates.
- County FIPS are 5-character strings with leading zeroes. Timestamps are timezone-aware UTC.
- Branches are `area/short-description`; commits are Conventional Commits (`feat(routing): ...`). Never commit to `main`.
- Run `make lint` and `make test` before calling anything done. Report failures with the output; never claim a check passed without running it.

## Product language

- Use: "Weather Safety Score", "comparative decision index", "lower modeled weather risk", "reduce exposure", "based on available weather data".
- Never: "safe route", "the safest route", "guaranteed safe", "zero risk", "the model knows the road will flood", "probability of surviving the trip". The top score band is never labeled "Safe".
- Official NWS alerts may raise risk, never lower it, and appear above any recommendation.

## Agent team

- `verifier` runs the checks and reports pass/fail. It never edits code.
- `code-reviewer` reviews a diff against the issue, ADRs, and schemas. It is read-only.
- `ux-claims-reviewer` reviews user-facing UI and text for accessibility and product language. It is read-only.
- `/work-issue <number>` runs the full loop: plan, implement, verify, review, fix, re-verify, hand off.
