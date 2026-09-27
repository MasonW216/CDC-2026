---
name: status
description: StormRoute progress triage. Reports where each issue stands, what is blocked or slipping against the hackathon gates, and drafts a short async team update. Use when the user asks for status, standup, "where are we", "what's next", or /status. Optional argument: an owner role (mason, cs, econ) to filter.
---

# StormRoute status and triage

Read-only: never edit issues, files, or branches. Output is a report and a draft message.

## 1. Gather

- **Issues.** `gh issue list -R MasonW216/CDC-2026 --state all --limit 100 --json number,title,state,labels,assignees,body`. If it returns none (issues not created yet), use `docs/issue_backlog.md` as the list and say so in the report.
- **Evidence of progress.** An issue counts as done only if it is closed or its acceptance criteria are visibly met in the code. Check `git log --oneline origin/main` and all branches (`git branch -a`, `git log --oneline origin/<branch> -10`), and look for the files each issue creates. Mark progress you infer from commits as "in progress (inferred)", never "done".
- **Dependencies.** Parse `Blocked by:` lines. Issues #7–#26 stay blocked until #6 (the EDA gate) closes.
- **Clock.** Read `.claude/event.json` for `start_utc`. If it is null, ask the user once for the hackathon start time and offer to save it there.

## 2. Gates (hours after start)

| Gate | Due | Must be true |
|---|---|---|
| 0 Lock-in | T+0:45 | scope signed off, schemas frozen, branches ready |
| A Feasibility | T+4 | NOAA events parsed; one route sampled into counties with arrival times; one label joined to a route window |
| B Model viability | T+8 | county-window table built; climatology + first model predictions; one real probability on a route segment |
| C Vertical slice | T+13 | site loads the cached replay with score, colored route, worst segment, one recommendation. Feature freeze |
| D Submission candidate | T+20 | tests pass; DevPost, README, deck, backup video |

Flag an item as **slipping** if its gate is less than 1 hour away and it isn't done, or if an open issue blocks something due at the next gate.

## 3. Report (to the user)

- One line: current time vs next gate, and on track / at risk / behind.
- **By person** (Mason, CS major, Econ/Stats major): done, in progress, next unblocked issue.
- **Slipping or blocked:** each with the reason and the one action that unblocks it.
- **Fallback check:** if Gate B is at risk, name the next unused step of the team's fallback ladder: (1) drop the boosted/stretch model, (2) keep the logistic baseline as the served model, (3) serve climatology for weaker hazards while flooding stays modeled. Alert floors ship regardless.

## 4. Draft team update

Draft a message to paste into the team chat, under 120 words: what landed, what's next, what's blocked and who can unblock it. Plain and friendly, no corporate tone. Don't send it anywhere; hand it to the user.
