/**
 * The Helene case-study page, against the real `prototype-score/1` shape
 * (artifacts/demo/helene_case_study.json, produced by the actual scoring pipeline).
 */
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import heleneCaseStudy from '../../../artifacts/demo/helene_case_study.json';
import HeleneCaseStudyPage from '../pages/HeleneCaseStudyPage';
import type { ScoreResponse } from '../types/score';

// react-leaflet needs a real layout engine it doesn't get in jsdom (see
// test/LiveRoutePage.test.tsx for the same, earlier precedent); the page logic under
// test here is data loading and page copy, not map rendering, so RouteMap is mocked to
// a simple summary.
vi.mock('../components/RouteMap', () => ({
  default: ({ route }: { route: { route_id: string } }) => (
    <div data-testid={`map-${route.route_id}`} />
  ),
}));

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, fetchHeleneCaseStudy: vi.fn(), fetchCountyBoundaries: vi.fn() };
});

import * as api from '../services/api';

const score = heleneCaseStudy as ScoreResponse;
const fetchHeleneCaseStudy = vi.mocked(api.fetchHeleneCaseStudy);
const fetchCountyBoundaries = vi.mocked(api.fetchCountyBoundaries);

function renderPage() {
  return render(
    <MemoryRouter>
      <HeleneCaseStudyPage />
    </MemoryRouter>,
  );
}

describe('HeleneCaseStudyPage', () => {
  beforeEach(() => {
    fetchHeleneCaseStudy.mockReset();
    fetchCountyBoundaries.mockReset();
    fetchCountyBoundaries.mockResolvedValue({ type: 'FeatureCollection', features: [] });
  });

  it('shows a loading state, then the fetched case study', async () => {
    fetchHeleneCaseStudy.mockResolvedValue(score);
    renderPage();
    expect(screen.getByRole('status')).toHaveTextContent(/loading/i);
    await waitFor(() => expect(screen.getAllByText(/severe concern/i).length).toBeGreaterThan(0));
  });

  it('clearly marks the page as historical, not a live trip result', async () => {
    fetchHeleneCaseStudy.mockResolvedValue(score);
    renderPage();
    await waitFor(() => screen.getByText(/historical replay, not a live trip result/i));
  });

  it('never claims a probability, a trained model, or a safety guarantee', async () => {
    fetchHeleneCaseStudy.mockResolvedValue(score);
    renderPage();
    await waitFor(() => expect(screen.getAllByText(/severe concern/i).length).toBeGreaterThan(0));
    expect(screen.queryByText(/safe route/i)).toBeNull();
    expect(screen.queryByText(/guaranteed safe/i)).toBeNull();
    expect(screen.queryByText(/probability of surviving/i)).toBeNull();
  });

  it('renders every route from the response', async () => {
    fetchHeleneCaseStudy.mockResolvedValue(score);
    renderPage();
    await waitFor(() => {
      for (let i = 0; i < score.routes.length; i += 1) {
        expect(screen.getByText(new RegExp(`Route ${i + 1}:`))).toBeTruthy();
      }
    });
  });

  it('shows an error state without crashing when the fetch fails', async () => {
    fetchHeleneCaseStudy.mockRejectedValue(new api.ApiError('Helene case study unavailable', 503));
    renderPage();
    await waitFor(() => screen.getByText(/helene case study unavailable/i));
  });
});
