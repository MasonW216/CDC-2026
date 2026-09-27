/**
 * Renders `route.contributing_factors` -- already structured server-side specifically for
 * this ("for an icon list", see types/score.ts), unrendered anywhere until now. A small
 * chip row: a rain glyph for `kind: 'rain'`, a warning-triangle glyph for `kind: 'alert'`,
 * a clock glyph for `kind: 'historical'` (the county's own 2015-2024 storm-event rate),
 * never anything else (that field's own contract note forbids inventing a new kind here,
 * e.g. "saturated ground", without a real backend input for it first).
 *
 * Plain characters, not an "AI" glyph or icon font -- matches the precedent already set
 * fixing the literal "AI" text bug elsewhere in this codebase.
 */
import { useState } from 'react';

import type { ContributingFactor } from '@/types/score';

const GLYPH: Record<ContributingFactor['kind'], string> = {
  rain: '🌧️',
  alert: '⚠️',
  historical: '🕰️',
};

function Chip({ factor }: { factor: ContributingFactor }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li>
      <button
        type="button"
        className="factor-chip"
        data-kind={factor.kind}
        aria-expanded={expanded}
        onClick={() => setExpanded((value) => !value)}
      >
        <span aria-hidden="true">{GLYPH[factor.kind]}</span>
        {factor.label}
        {factor.kind === 'rain' ? `, ${factor.county_name}` : ''}
      </button>
      {expanded && <p className="note">{factor.detail}</p>}
    </li>
  );
}

export default function ContributingFactorChips({ factors }: { factors: ContributingFactor[] }) {
  if (factors.length === 0) return null;
  return (
    <ul className="factor-chip-row" aria-label="What is driving this route's indicated concern">
      {factors.map((factor) => (
        <Chip key={`${factor.county_name}-${factor.kind}-${factor.arrival_utc}`} factor={factor} />
      ))}
    </ul>
  );
}
