/**
 * RouteComparisonChart: must only render a real, distinguishable-or-tie comparison, and
 * must never visually invent a "winner" the backend itself declined to claim.
 */
import { render } from '@testing-library/react';

import RouteComparisonChart from '../components/RouteComparisonChart';
import type { Comparison, RouteScore } from '../types/score';

function route(id: string, index: number | null, band: RouteScore['band']): RouteScore {
  return {
    route_id: id,
    duration_minutes: 100,
    distance_km: 100,
    status: index === null ? 'unassessed' : 'assessed',
    index,
    band,
    is_lower_bound: false,
    minutes_at_or_above_50: 0,
    highest_concern_segment: null,
    segments: [],
    alerts: [],
    reasons: [],
    contributing_factors: [],
    geometry: null,
  };
}

const baseComparison: Comparison = {
  ranking: 'distinguishable',
  fastest_route_id: 'a',
  lowest_concern_route_id: 'b',
  extra_minutes: 5,
  index_difference: 40,
  message: 'b shows lower indicated concern.',
  severe_advice: null,
};

describe('RouteComparisonChart', () => {
  it('renders a bar per route for a distinguishable comparison', () => {
    const routes = [route('a', 80, 'Severe concern'), route('b', 20, 'Lower concern')];
    const { container } = render(
      <RouteComparisonChart
        routes={routes}
        comparison={baseComparison}
        labels={{ a: 'Route 1', b: 'Route 2' }}
      />,
    );
    expect(container.querySelector('.comparison-chart')).toBeTruthy();
  });

  it('does not render for an unavailable ranking (no confident comparison to show)', () => {
    const routes = [route('a', 80, 'Severe concern'), route('b', null, 'Not assessed')];
    const comparison: Comparison = {
      ...baseComparison,
      ranking: 'unavailable',
      lowest_concern_route_id: null,
    };
    const { container } = render(
      <RouteComparisonChart
        routes={routes}
        comparison={comparison}
        labels={{ a: 'Route 1', b: 'Route 2' }}
      />,
    );
    expect(container.querySelector('.comparison-chart')).toBeNull();
  });

  it('does not render for a single route', () => {
    const routes = [route('a', 80, 'Severe concern')];
    const comparison: Comparison = {
      ...baseComparison,
      ranking: 'single_route',
      lowest_concern_route_id: null,
    };
    const { container } = render(
      <RouteComparisonChart routes={routes} comparison={comparison} labels={{ a: 'Route 1' }} />,
    );
    expect(container.querySelector('.comparison-chart')).toBeNull();
  });

  it('renders for a tie (equal bars, no invented winner in the chart itself)', () => {
    const routes = [route('a', 50, 'High concern'), route('b', 48, 'High concern')];
    const comparison: Comparison = {
      ...baseComparison,
      ranking: 'tie',
      lowest_concern_route_id: null,
    };
    const { container } = render(
      <RouteComparisonChart
        routes={routes}
        comparison={comparison}
        labels={{ a: 'Route 1', b: 'Route 2' }}
      />,
    );
    expect(container.querySelector('.comparison-chart')).toBeTruthy();
  });
});
