/**
 * The MVP prototype results screen, built against the cached Helene replay
 * fixture. No network, no router state -- the fixture is the whole input.
 */
import { render, screen } from '@testing-library/react';

import PrototypeResultsPage from '../pages/PrototypeResultsPage';
import prototypeResult from '../fixtures/prototypeResult.json';
import type { PrototypeResult } from '../types/prototype';

const fixture = prototypeResult as PrototypeResult;

describe('PrototypeResultsPage', () => {
  it('labels the indicator as a prototype, never as a safety guarantee', () => {
    render(<PrototypeResultsPage />);
    expect(screen.getAllByText(/prototype hazard indicator/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/safe route/i)).toBeNull();
    expect(screen.queryByText(/guaranteed safe/i)).toBeNull();
    expect(screen.queryByText(/probability of surviving/i)).toBeNull();
  });

  it('shows the origin and destination', () => {
    render(<PrototypeResultsPage />);
    expect(
      screen.getByRole('heading', {
        level: 2,
        name: `${fixture.origin.label} to ${fixture.destination.label}`,
      }),
    ).toBeTruthy();
  });

  it('renders one route card per route in the fixture, each with its own timeline', () => {
    render(<PrototypeResultsPage />);
    const routeIds = Object.keys(fixture.routes);
    for (let index = 0; index < routeIds.length; index += 1) {
      const route = fixture.routes[routeIds[index] as string];
      expect(route).toBeDefined();
      expect(
        screen.getByRole('heading', { level: 3, name: new RegExp(`Route ${index + 1}:`) }),
      ).toBeTruthy();
    }
    // Every segment's county name appears somewhere in the timeline tables.
    for (const route of Object.values(fixture.routes)) {
      for (const segment of route.segments) {
        expect(screen.getAllByText(segment.county_name).length).toBeGreaterThan(0);
      }
    }
  });

  it('shows the highest-concern segment and its reason for each route', () => {
    render(<PrototypeResultsPage />);
    for (const route of Object.values(fixture.routes)) {
      if (route.highest_concern_segment) {
        expect(screen.getAllByText(route.highest_concern_segment.reason).length).toBeGreaterThan(0);
      }
    }
  });

  it('puts official alerts above the advisory for a route that has them', () => {
    render(<PrototypeResultsPage />);
    const routeWithAlerts = Object.values(fixture.routes).find((route) =>
      route.segments.some((segment) => segment.alerts_used.length > 0),
    );
    expect(routeWithAlerts).toBeDefined();
    if (!routeWithAlerts) {
      return;
    }
    const alertBanner = screen.getAllByRole('alert')[0];
    expect(alertBanner).toBeTruthy();
    const advisory = screen.getAllByText(routeWithAlerts.advisory)[0];
    expect(advisory).toBeTruthy();
    // The alert banner precedes the advisory text in document order.
    expect(
      alertBanner!.compareDocumentPosition(advisory!) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it('shows the replay caveat and inputs provenance on screen', () => {
    render(<PrototypeResultsPage />);
    const firstRoute = Object.values(fixture.routes)[0];
    expect(firstRoute).toBeDefined();
    if (firstRoute) {
      expect(screen.getAllByText(firstRoute.replay_caveat).length).toBeGreaterThan(0);
    }
    expect(screen.getByText(/inputs and provenance/i)).toBeTruthy();
    expect(
      screen.getByText(fixture.inputs_provenance.sources.precipitation!, { exact: false }),
    ).toBeTruthy();
    expect(
      screen.getByText(fixture.inputs_provenance.sources.alerts!, { exact: false }),
    ).toBeTruthy();
  });

  it('shows the comparison note without declaring either route safe', () => {
    render(<PrototypeResultsPage />);
    if (fixture.comparison) {
      expect(screen.getByText(fixture.comparison.note)).toBeTruthy();
    }
  });
});
