/**
 * Non-component helpers for rendering a `prototype-score/1` response.
 *
 * Split from components/ScoreDisplay.tsx (which stays component-only, matching this
 * project's react-refresh convention -- see utils/departureTime.ts for the precedent).
 */

export const BAND_CLASS: Record<string, string> = {
  'Lower concern': 'level-badge--0',
  'Elevated concern': 'level-badge--1',
  'High concern': 'level-badge--2',
  'Severe concern': 'level-badge--3',
  'Not assessed': 'level-badge--none',
};

/** A band's concern level, for anything that needs the numeric `--level-N-fg` token. */
export const BAND_LEVEL: Record<string, 0 | 1 | 2 | 3 | 'none'> = {
  'Lower concern': 0,
  'Elevated concern': 1,
  'High concern': 2,
  'Severe concern': 3,
  'Not assessed': 'none',
};

export function formatInstant(iso: string): string {
  return `${new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))} UTC`;
}
