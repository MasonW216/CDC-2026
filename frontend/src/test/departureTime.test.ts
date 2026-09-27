import { describe, expect, it } from 'vitest';

import { toEasternIso } from '../utils/departureTime';

describe('toEasternIso', () => {
  it('uses the EDT offset in September, matching the build guide example', () => {
    expect(toEasternIso('2024-09-27T12:00')).toBe('2024-09-27T12:00:00-04:00');
  });

  it('uses the EST offset in January', () => {
    expect(toEasternIso('2024-01-15T09:30')).toBe('2024-01-15T09:30:00-05:00');
  });

  it('defaults seconds to :00 when the input omits them', () => {
    expect(toEasternIso('2024-01-15T09:30')).toContain(':00-05:00');
  });

  it('preserves seconds when the input has them', () => {
    expect(toEasternIso('2024-09-27T12:00:45')).toBe('2024-09-27T12:00:45-04:00');
  });

  it('rejects a value with no time component', () => {
    expect(() => toEasternIso('2024-09-27')).toThrow(/datetime-local/);
  });

  it('rejects an empty value', () => {
    expect(() => toEasternIso('')).toThrow();
  });
});
