/**
 * The live map view. Both live endpoints (routing, scoring) are mocked, so
 * these tests exercise the route/score matching and coloring logic without
 * depending on real weather to produce a distinguishable result on demand.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import LiveRoutePage from '../pages/LiveRoutePage';
import * as api from '../services/api';
import type { Location } from '../types/trip';

const ASHEVILLE = { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 };
const CHARLOTTE = { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 };
const KNOWN_PLACES: Record<string, Location> = {
  [ASHEVILLE.label]: ASHEVILLE,
  [CHARLOTTE.label]: CHARLOTTE,
};

vi.mock('../components/LocationSearch', () => ({
  default: ({
    id,
    label,
    onChange,
  }: {
    id: string;
    label: string;
    onChange: (value: Location | null) => void;
  }) => (
    <div>
      <label htmlFor={id}>{label}</label>
      <input id={id} onChange={(e) => onChange(KNOWN_PLACES[e.target.value] ?? null)} />
    </div>
  ),
}));

// react-leaflet needs a real layout engine it doesn't get in jsdom; the
// coloring/matching logic under test lives in LiveRoutePage, not the map
// rendering itself, so the map component is mocked to a simple summary.
vi.mock('../components/LiveRouteMap', () => ({
  default: ({ routes }: { routes: { id: string; color: string }[] }) => (
    <div data-testid="map">
      {routes.map((r) => (
        <div key={r.id} data-testid={`route-${r.id}`} data-color={r.color}>
          {r.id}
        </div>
      ))}
    </div>
  ),
}));

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, fetchRoute: vi.fn(), scoreTrip: vi.fn() };
});

const fetchRoute = vi.mocked(api.fetchRoute);
const scoreTrip = vi.mocked(api.scoreTrip);

const ROUTE_RESPONSE = {
  routes: [
    {
      route_id: 'route_0',
      coordinates: [
        [-82.55, 35.6],
        [-80.84, 35.23],
      ] as [number, number][],
      duration_minutes: 150,
      distance_km: 200,
    },
    {
      route_id: 'route_1',
      coordinates: [
        [-82.55, 35.6],
        [-81.0, 35.4],
        [-80.84, 35.23],
      ] as [number, number][],
      duration_minutes: 160,
      distance_km: 210,
    },
  ],
};

function scoreWith(comparison: Record<string, unknown>) {
  return {
    schema_version: 'prototype-score/1',
    score_name: 'test',
    mode: 'live',
    requested_at_utc: '2026-09-27T12:00:00Z',
    departure_utc: '2026-09-27T15:00:00Z',
    routes: [
      {
        route_id: 'route_0',
        duration_minutes: 150,
        distance_km: 200,
        status: 'assessed',
        index: 10,
        band: 'Lower concern',
        is_lower_bound: false,
        minutes_at_or_above_50: 0,
        highest_concern_segment: null,
        segments: [],
        alerts: [],
        reasons: [],
      },
      {
        route_id: 'route_1',
        duration_minutes: 160,
        distance_km: 210,
        status: 'assessed',
        index: 70,
        band: 'High concern',
        is_lower_bound: false,
        minutes_at_or_above_50: 0,
        highest_concern_segment: null,
        segments: [],
        alerts: [],
        reasons: [],
      },
    ],
    comparison,
    coverage: {
      forecast: {
        source: 'test',
        retrieved_utc: '2026-09-27T12:00:00Z',
        horizon_hours: 96,
        missing_counties: [],
        from_cache: false,
        error: null,
      },
      alerts: {
        source: 'test',
        retrieved_utc: '2026-09-27T12:00:00Z',
        ok: true,
        error: null,
        from_cache: false,
        unmapped_alerts: 0,
        flood_alerts_in_effect_statewide: 0,
      },
      geography: { supported: true, message: null },
    },
    alerts: [],
    limitations: [],
  };
}

async function submitTrip(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Origin'), ASHEVILLE.label);
  await user.type(screen.getByLabelText('Destination'), CHARLOTTE.label);
  await user.type(screen.getByLabelText(/departure date and time/i), '2026-10-01T09:00');
  await user.click(screen.getByRole('button', { name: /analyze trip/i }));
}

describe('LiveRoutePage', () => {
  beforeEach(() => {
    fetchRoute.mockReset();
    scoreTrip.mockReset();
    fetchRoute.mockResolvedValue(ROUTE_RESPONSE);
  });

  it('shows the trip form before any submission', () => {
    render(<LiveRoutePage />);
    expect(screen.getByLabelText('Origin')).toBeTruthy();
    expect(screen.getByLabelText('Destination')).toBeTruthy();
  });

  it('colors the lower-concern route green and the other red when distinguishable', async () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    scoreTrip.mockResolvedValue(
      scoreWith({
        ranking: 'distinguishable',
        fastest_route_id: 'route_0',
        lowest_concern_route_id: 'route_0',
        extra_minutes: 10,
        index_difference: 60,
        message: 'Route 1 shows a lower indicated concern.',
        severe_advice: null,
      }) as never,
    );
    const user = userEvent.setup();
    render(<LiveRoutePage />);
    await submitTrip(user);
    expect(await screen.findByTestId('map')).toBeTruthy();
    expect(screen.getByTestId('route-route_0').dataset.color).toBe('var(--level-0-fg, #157347)');
    expect(screen.getByTestId('route-route_1').dataset.color).toBe('var(--level-3-fg, #b3261e)');
    expect(screen.getByText(/lower modeled weather risk/i)).toBeTruthy();
    expect(screen.getByText(/higher modeled weather risk/i)).toBeTruthy();
  });

  it('does not invent a winner on a tie: both routes get the same neutral color', async () => {
    scoreTrip.mockResolvedValue(
      scoreWith({
        ranking: 'tie',
        fastest_route_id: 'route_0',
        lowest_concern_route_id: null,
        extra_minutes: null,
        index_difference: null,
        message: 'The routes show similar indicated concern, so this index does not favor one.',
        severe_advice: null,
      }) as never,
    );
    const user = userEvent.setup();
    render(<LiveRoutePage />);
    await submitTrip(user);
    expect(await screen.findByTestId('map')).toBeTruthy();
    const color0 = screen.getByTestId('route-route_0').dataset.color;
    const color1 = screen.getByTestId('route-route_1').dataset.color;
    expect(color0).toBe(color1);
    expect(screen.queryByText(/lower modeled weather risk/i)).toBeNull();
    expect(document.body.textContent?.toLowerCase()).not.toContain('safer');
  });

  it('shows an inline error instead of a map when scoring fails', async () => {
    scoreTrip.mockRejectedValue(new api.ApiError('departure_time must be in the future', 422));
    const user = userEvent.setup();
    render(<LiveRoutePage />);
    await submitTrip(user);
    expect(await screen.findByRole('alert')).toHaveTextContent(
      /departure_time must be in the future/i,
    );
    expect(screen.queryByTestId('map')).toBeNull();
  });
});
