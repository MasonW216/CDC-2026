# Contributing to StormRoute

This is a three-person team working against a competition deadline. The rules
below exist so that the repository stays trustworthy while we move quickly.

Two documents govern the work:

- [docs/build_guide.md](docs/build_guide.md) — the authoritative build order, milestones, and acceptance criteria
- [docs/project_specification.md](docs/project_specification.md) — the original product and technical specification

Where the two disagree, the build guide wins. See
[docs/adr/0000-specification-precedence.md](docs/adr/0000-specification-precedence.md).

---

## The one rule that outranks the others

**No production modeling, scoring, API, or website code lands before the
Milestone 2 EDA verification gate is approved.**

Repository setup and the minimal data-download utilities that make the EDA
reproducible are the only exceptions. If you are unsure whether your work is
allowed yet, it probably is not — ask in the issue first.

---

## Getting set up

```bash
gh repo clone OWNER/stormroute && cd stormroute
cp .env.example .env
make setup
make test
```

Prefer a GitHub Codespace. The dev container pins Python 3.11, Node 20, and the
geospatial system libraries, so "works on my machine" stops being a category of
bug. See [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json).

Run `make help` to see every available command.

---

## Branches

Never commit directly to `main` after Milestone 0. Use short-lived branches
named `area/short-description`:

```text
chore/repository-scaffold
data/county-windows
eda/noaa-profile
model/calibrated-xgb
geo/route-sampling
api/trip-score
web/results-page
docs/model-card
fix/leading-zero-fips
```

Rebase or update your branch before requesting final review.

---

## Commits

Conventional Commit style. The type describes the kind of change; the scope
names the area.

```text
chore(repo): scaffold reproducible Codespaces environment
data(noaa): add reproducible Storm Events download
eda(storms): profile NC flood labels from 2015 to 2024
feat(model): train calibrated monotonic hazard classifier
feat(scoring): aggregate county-window risks across a route
test(api): cover alert-floor behavior
docs(model): publish evaluation and limitations
fix(data): preserve leading zeroes in county FIPS
```

Types in use: `chore`, `data`, `eda`, `feat`, `fix`, `test`, `docs`, `analysis`.

Every commit should leave the branch runnable. Messages such as `updates`,
`stuff`, `final`, or `fixes` will be sent back.

---

## Pull requests

One logical outcome per pull request. Fill in
[the template](.github/PULL_REQUEST_TEMPLATE.md) — it is short on purpose.

### Definition of done

A pull request is ready to merge only when:

- [ ] its issue and acceptance criteria are linked;
- [ ] it contains one coherent outcome;
- [ ] new code includes appropriate tests;
- [ ] data or model changes include updated documentation;
- [ ] generated outputs are reproducible from a command in the `Makefile`;
- [ ] notebook cells execute in order from a restarted kernel;
- [ ] CI passes;
- [ ] no secrets, raw data, or personal absolute paths are present;
- [ ] screenshots or metric files are attached when behavior is visual or analytical;
- [ ] a non-author teammate has reviewed it; and
- [ ] no conversation is left unresolved.

Squash-merge ordinary feature branches.

---

## What must never be committed

- `.env` files, API tokens, deployment credentials
- anything under `data/raw/`, `data/interim/`, or `data/processed/`
- `node_modules/`, `.venv/`, caches
- model binaries (`*.joblib`) — the manifest and its checksum are tracked instead
- absolute local paths, such as anything under a teammate's `~/Downloads`

Every path in code and notebooks resolves from the repository root or from
configuration. If a notebook only runs on your laptop, it is broken.

---

## Code standards

**Python.** Ruff formats and lints; Mypy runs in strict mode. Every module
carries a docstring saying what it is responsible for. Run `make lint` before
pushing; `pre-commit` catches most of it at commit time.

**TypeScript.** ESLint and Prettier, `tsc --noEmit` for types. Components stay
presentational where practical; API shapes live in `frontend/src/types/`.

**Notebooks.** Markdown before each analytical section stating the question, and
a short conclusion after the result. Outputs are stripped by `nbstripout`;
figures are exported to `outputs/figures/` with stable filenames.

---

## Tests

Coverage percentage is not the target. These areas are:

- scoring formulas and the official-alert floor — near-total coverage
- every leakage rule — a direct test each
- API request/response contracts
- score and recommendation display components
- one end-to-end cached demo flow

Add a regression test with every bug fix.

---

## Reviewing

Reviewers own the claim, not only the code. When reviewing analysis, check that
what the text asserts is what the numbers show. "The chart does not support this
sentence" is one of the most valuable comments you can leave on this project.

The ownership and required-reviewer map is in
[docs/build_guide.md](docs/build_guide.md), section 18.
