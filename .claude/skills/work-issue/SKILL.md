---
name: work-issue
description: Take one StormRoute GitHub issue from plan to a reviewed, verified branch ready for a human to push. Use when the user says "work on #N", "do issue N", or /work-issue N.
---

# Work one issue end to end

Argument: the issue number. If none was given, ask for it.

## 1. Understand
- Read the issue (`gh issue view <n>`, or its section in `docs/issue_backlog.md`), the build-guide section it cites, and any ADR it touches.
- Check `Blocked by:`. If a blocker is open, or the issue is production code and the EDA gate (#6) is not approved, stop and say so.
- Restate the acceptance criteria as a checklist. Ask the user about anything ambiguous before writing code.

## 2. Plan
- Short plan: files to create or change, tests to write first, anything that touches a schema or contract. Flag schema or structure changes as needing team agreement.
- Get the user's OK on the plan for anything bigger than a small fix.

## 3. Implement
- Branch: stay on the current working branch unless the user asks for a new one (`area/short-description` from `origin/main`).
- Write the tests for the acceptance criteria first, then the code. Keep the change to this issue only.

## 4. Verify, then review
- Launch the `verifier` subagent. On FAIL, fix and re-run until PASS. Don't argue with the output.
- Launch `code-reviewer` (and `ux-claims-reviewer` if anything user-facing changed) in parallel, giving them the issue number and base branch.
- Fix every Must fix / Blocking item. For each Should fix, either fix it or note why not. Put team questions in front of the user rather than deciding them.
- Re-run `verifier` after fixes.

## 5. Hand off
- Commit with Conventional Commits.
- Give the user: the acceptance checklist with evidence, the verifier verdict, the review verdicts and what changed because of them, open questions, and a draft PR description (reviewer: the issue's listed reviewer). The user reviews the diff and pushes; don't push unless they say to.
