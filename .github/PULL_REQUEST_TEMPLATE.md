## Outcome

<!-- What now works, or what was learned. One or two sentences. -->

Closes #

## Evidence

<!--
Tests, figures, screenshots, metric files, or command output. Analytical and
visual changes need evidence a reviewer can see without running the branch.
-->

## Data/model impact

<!--
Schemas, source versions, splits, or artifacts changed. Write "None" if nothing
changed. If a schema changed, confirm docs/data_card.md and the validation
tests were updated with it.
-->

## Risks and limitations

<!--
Known gaps, anything a reviewer should look at hardest, and follow-up issues.
"None" is rarely the honest answer.
-->

## Checklist

- [ ] Tests pass locally (`make test`)
- [ ] Lint and types pass locally (`make lint`)
- [ ] Documentation updated
- [ ] No secrets, raw data, or absolute local paths committed
- [ ] Notebook cells execute in order from a restarted kernel (or N/A)
- [ ] Acceptance criteria on the linked issue are met
- [ ] This work is permitted at the current milestone (EDA gate respected)
