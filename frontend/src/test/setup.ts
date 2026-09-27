/**
 * Vitest setup.
 *
 * Registers @testing-library/jest-dom matchers and resets the DOM between tests.
 * Any network call in a component test is a bug: the API client is mocked here.
 */
import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
});

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => {
      throw new Error('Network call attempted in a component test. Mock the API client instead.');
    }),
  );
  // jsdom has no layout engine, so it never implements ResizeObserver; recharts'
  // <ResponsiveContainer> (RouteComparisonChart) requires one to exist, even though it
  // never fires a real resize in a test. A no-op stub is enough.
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
});
