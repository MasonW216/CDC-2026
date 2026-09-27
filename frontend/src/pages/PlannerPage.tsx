/**
 * Trip planner page.
 *
 * Page chrome (heading, safety disclaimer, saved-trip shortcut) around
 * TripForm, which owns origin/destination search, departure-time input and
 * validation, and always submits `mode: 'live'`. The disclaimer is visible
 * before the user submits, not after.
 *
 * Submits to POST /api/v1/trips/score. The saved-trip button scores the
 * hardcoded DEMO_SCENARIO directly, bypassing TripForm entirely -- it never
 * fills the form or reads its state. That is deliberate: an earlier version
 * filled the form and inferred the mode from "was demo loaded", which broke
 * the moment someone loaded the demo and then edited a field (still
 * cached_replay, but scoring whatever they'd typed). Two independent paths
 * with no shared state cannot have that bug. Both render through the same
 * PrototypeResultsPage, using the same `score.ts` contract.
 *
 * The saved trip is a contemporary replay (artifacts/demo/saved_trip_request.json),
 * not Hurricane Helene -- the button and copy used to claim otherwise; fixed
 * per the team's frontend handoff. The separate, real Helene replay lives at
 * /case-studies/helene and is never reachable from here.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import TripForm from '@/components/TripForm';
import { useHeaderSearch } from '@/contexts/HeaderSearchContext';
import { ApiError, scoreTrip } from '@/services/api';
import { toEasternIso } from '@/utils/departureTime';
import type { Location, TripRequest } from '@/types/trip';

// Mirrors artifacts/demo/saved_trip_request.json's own origin/destination/time
// closely enough for the button's label; the backend ignores these submitted
// values for mode: 'cached_replay' and always serves its own saved trip.
const DEMO_SCENARIO: { origin: Location; destination: Location; departureLocal: string } = {
  origin: { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 },
  destination: { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 },
  departureLocal: '2024-09-27T12:00',
};

export default function PlannerPage() {
  const navigate = useNavigate();
  const { searchedLocation } = useHeaderSearch();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function score(request: TripRequest) {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await scoreTrip(request);
      navigate('/results', {
        state: {
          score: result,
          request: { origin: request.origin, destination: request.destination },
        },
      });
    } catch (error) {
      setSubmitError(error instanceof ApiError ? error.message : 'Could not score this trip.');
    } finally {
      setSubmitting(false);
    }
  }

  function runSavedTripReplay() {
    void score({
      origin: DEMO_SCENARIO.origin,
      destination: DEMO_SCENARIO.destination,
      departure_time: toEasternIso(DEMO_SCENARIO.departureLocal),
      mode: 'cached_replay',
    });
  }

  function handleFormSubmit(request: TripRequest) {
    void score({ ...request, mode: 'live' });
  }

  return (
    <section aria-labelledby="planner-heading">
      <h2 id="planner-heading" className="page-title">
        Plan a trip
      </h2>
      <p role="note" className="note">
        StormRoute compares the modeled weather-hazard exposure of routes and departure times based
        on available weather data. It is a comparative decision index, not a guarantee of safety,
        and it never overrides an official National Weather Service warning. Type a real, future
        trip above to score it live; the saved-trip button below replays a cached, offline example
        instead of calling live weather. For a real historical storm, see the Helene case study. For
        current conditions and official warnings, visit weather.gov.
      </p>

      <div className="card" style={{ marginTop: 'var(--space-4)' }}>
        <TripForm onSubmit={handleFormSubmit} initialOrigin={searchedLocation} />

        <button
          type="button"
          onClick={runSavedTripReplay}
          disabled={submitting}
          className="btn"
          style={{ width: '100%', marginTop: 'var(--space-3)' }}
        >
          Load saved trip (offline demo)
        </button>

        {submitting && (
          <p role="status" className="note">
            Scoring this trip&hellip;
          </p>
        )}
        {submitError && <p role="alert">{submitError}</p>}
      </div>
    </section>
  );
}
