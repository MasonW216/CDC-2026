/**
 * The trip results screen, against the real `prototype-score/1` shape
 * (artifacts/demo/saved_trip_response.json, produced by the actual scoring
 * pipeline -- not hand-crafted fixture data).
 */
import { act, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';

import savedTripResponse from '../../../artifacts/demo/saved_trip_response.json';
import PrototypeResultsPage from '../pages/PrototypeResultsPage';
import type { RouteScore, ScoreResponse } from '../types/score';

// react-leaflet needs a real layout engine it doesn't get in jsdom (see
// test/LiveRoutePage.test.tsx). Renders enough of the route's real data (county names)
// that tests can still verify the right route reached the map, without a real Leaflet
// mount.
vi.mock('../components/RouteMap', () => ({
  default: ({ route }: { route: RouteScore }) => (
    <div data-testid={`map-${route.route_id}`}>
      {route.segments.map((s) => (
        <span key={`${s.county_fips}-${s.arrival_utc}`}>{s.county_name}</span>
      ))}
    </div>
  ),
}));

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    fetchCountyBoundaries: vi.fn().mockResolvedValue({ type: 'FeatureCollection', features: [] }),
  };
});

const score = savedTripResponse as ScoreResponse;
const request = {
  origin: { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 },
  destination: { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 },
};

async function renderAtResults(state: unknown) {
  const result = render(
    <MemoryRouter initialEntries={[{ pathname: '/results', state }]}>
      <Routes>
        <Route path="/results" element={<PrototypeResultsPage />} />
        <Route path="/" element={<p>planner placeholder</p>} />
      </Routes>
    </MemoryRouter>,
  );
  // Flush the county-boundaries fetch (a mocked resolved promise) so its state update
  // happens inside act(), not after the test's assertions have already run.
  await act(async () => {});
  return result;
}

describe('PrototypeResultsPage', () => {
  it('shows a plan-a-trip message when there is no navigation state', async () => {
    await renderAtResults(null);
    expect(screen.getByText(/no trip to show yet/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /plan a trip/i })).toBeTruthy();
  });

  it('labels the indicator as a prototype, never as a safety guarantee', async () => {
    await renderAtResults({ score, request });
    expect(screen.getAllByText(/prototype hazard indicator/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/safe route/i)).toBeNull();
    expect(screen.queryByText(/guaranteed safe/i)).toBeNull();
    expect(screen.queryByText(/probability of surviving/i)).toBeNull();
  });

  it('shows the origin and destination from the request, not the score response', async () => {
    await renderAtResults({ score, request });
    expect(
      screen.getByRole('heading', {
        level: 2,
        name: `${request.origin.label} to ${request.destination.label}`,
      }),
    ).toBeTruthy();
  });

  it('renders one route card per route, each with a band-labeled index', async () => {
    await renderAtResults({ score, request });
    score.routes.forEach((_route, index) => {
      expect(
        screen.getByRole('heading', { level: 3, name: new RegExp(`Route ${index + 1}:`) }),
      ).toBeTruthy();
    });
    for (const route of score.routes) {
      for (const segment of route.segments) {
        expect(screen.getAllByText(segment.county_name).length).toBeGreaterThan(0);
      }
    }
  });

  it('shows the comparison message and, when present, severe advice', async () => {
    await renderAtResults({ score, request });
    expect(screen.getByText(score.comparison.message)).toBeTruthy();
    if (score.comparison.severe_advice) {
      expect(screen.getByText(score.comparison.severe_advice)).toBeTruthy();
    }
  });

  it('never claims a lower-concern route on a tie', async () => {
    const tied: ScoreResponse = {
      ...score,
      comparison: {
        ranking: 'tie',
        fastest_route_id: score.routes[0]?.route_id ?? null,
        lowest_concern_route_id: null,
        extra_minutes: null,
        index_difference: null,
        message: 'The routes show similar indicated concern, so this index does not favor one.',
        severe_advice: null,
      },
    };
    await renderAtResults({ score: tied, request });
    expect(document.body.textContent?.toLowerCase()).not.toContain('safer');
  });

  it('shows known limitations when the response carries any', async () => {
    await renderAtResults({ score, request });
    if (score.limitations.length > 0) {
      expect(screen.getByText(/known limits/i)).toBeTruthy();
      expect(screen.getByText(score.limitations[0]!)).toBeTruthy();
    }
  });
});
