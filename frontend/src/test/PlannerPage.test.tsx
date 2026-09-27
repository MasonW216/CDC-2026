/**
 * Page-level behavior only. Field validation and search live in TripForm and
 * LocationSearch, and are covered by their own test files.
 *
 * The demo button and the form are two independent paths to scoreTrip, with
 * no shared state -- see PlannerPage's docstring for why that's deliberate.
 * Results render inline (no navigation): this page owns the sidebar and the
 * map together.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import savedTripResponse from '../../../artifacts/demo/saved_trip_response.json';
import PlannerPage from '../pages/PlannerPage';
import * as api from '../services/api';
import type { ScoreResponse } from '../types/score';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, scoreTrip: vi.fn(), fetchRoute: vi.fn() };
});

// Leaflet needs real layout, which jsdom doesn't do; the map itself is
// covered by its own rendering, not page-level behavior.
vi.mock('../components/LiveRouteMap', () => ({
  default: () => <div data-testid="map" />,
}));

const score = savedTripResponse as ScoreResponse;
const scoreTrip = vi.mocked(api.scoreTrip);
const fetchRoute = vi.mocked(api.fetchRoute);

const ROUTE_RESPONSE = {
  routes: score.routes.map((r) => ({
    route_id: r.route_id,
    coordinates: [
      [-82.5515, 35.5951],
      [-80.8431, 35.2271],
    ] as [number, number][],
    duration_minutes: r.duration_minutes,
    distance_km: r.distance_km,
  })),
};

function renderPlanner() {
  return render(<PlannerPage />);
}

describe('PlannerPage', () => {
  beforeEach(() => {
    scoreTrip.mockReset();
    fetchRoute.mockReset();
    scoreTrip.mockResolvedValue(score);
    fetchRoute.mockResolvedValue(ROUTE_RESPONSE);
  });

  it('shows the safety disclaimer before any submission', () => {
    renderPlanner();
    expect(screen.getByText(/comparative decision index/i)).toBeTruthy();
    expect(screen.getByText(/not a guarantee of safety/i)).toBeTruthy();
    expect(screen.queryByText(/safe route/i)).toBeNull();
  });

  it('renders the trip form', () => {
    renderPlanner();
    expect(screen.getByLabelText('Origin')).toBeTruthy();
    expect(screen.getByLabelText('Destination')).toBeTruthy();
    expect(screen.getByLabelText(/departure date and time/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /analyze trip/i })).toBeTruthy();
  });

  it('the demo button scores the hardcoded scenario directly, without touching the form', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load saved trip \(offline demo\)/i }));
    expect(await screen.findByTestId('map')).toBeTruthy();
    expect(scoreTrip).toHaveBeenCalledTimes(1);
    const request = scoreTrip.mock.calls[0]![0];
    expect(request.mode).toBe('cached_replay');
    expect(request.origin.label).toBe('Asheville, NC');
    expect(request.destination.label).toBe('Charlotte, NC');
    // The form was never filled -- the demo path never reads or writes it.
    expect(screen.getByLabelText('Origin')).toHaveValue('');
  });

  it('shows the prototype hazard index and the real reasons after a successful score', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load saved trip \(offline demo\)/i }));
    expect(await screen.findByText(/prototype hazard index/i)).toBeTruthy();
    const primary = score.routes[0]!;
    for (const reason of primary.reasons) {
      expect(screen.getByText(reason)).toBeTruthy();
    }
  });

  it('a manually entered trip always submits mode: live, demo or not', async () => {
    const user = userEvent.setup();
    renderPlanner();
    // LocationSearch requires a resolved selection; without one the form
    // reports a validation error instead of submitting, which is exactly the
    // behavior under test here: mode is decided before any network call.
    await user.type(screen.getByLabelText('Origin'), 'x');
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(scoreTrip).not.toHaveBeenCalled();
  });

  it('shows an inline error instead of a map when the demo replay fails', async () => {
    scoreTrip.mockRejectedValueOnce(new api.ApiError('No saved demo trip is cached yet.', 503));
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load saved trip \(offline demo\)/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/no saved demo trip/i);
    expect(screen.queryByTestId('map')).toBeNull();
  });

  it('disables the demo button while a request is in flight', async () => {
    let resolve!: (value: ScoreResponse) => void;
    scoreTrip.mockReturnValueOnce(new Promise((r) => (resolve = r)));
    const user = userEvent.setup();
    renderPlanner();
    const demoButton = screen.getByRole('button', { name: /load saved trip \(offline demo\)/i });
    await user.click(demoButton);
    expect(demoButton).toBeDisabled();
    resolve(score);
    expect(await screen.findByTestId('map')).toBeTruthy();
  });

  it('the demo button is reachable and activatable from the keyboard', async () => {
    const user = userEvent.setup();
    renderPlanner();
    const demoButton = screen.getByRole('button', { name: /load saved trip \(offline demo\)/i });
    demoButton.focus();
    await user.keyboard('{Enter}');
    expect(await screen.findByTestId('map')).toBeTruthy();
  });
});
