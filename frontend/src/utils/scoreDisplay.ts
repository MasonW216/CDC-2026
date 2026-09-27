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

export function formatInstant(iso: string): string {
  return `${new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))} UTC`;
}
