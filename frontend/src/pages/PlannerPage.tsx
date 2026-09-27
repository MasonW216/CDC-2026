/**
 * Trip planner page.
 *
 * Page chrome (heading, safety disclaimer, demo-scenario shortcut) around
 * TripForm, which owns origin/destination search, departure-time input and
 * validation, and always submits `mode: 'live'`. The disclaimer is visible
 * before the user submits, not after.
 *
 * Submits to POST /api/v1/trips/score. The "Load saved demo trip" button scores the
 * hardcoded DEMO_SCENARIO directly with `mode: 'cached_replay'` (the brief's offline
 * fallback: a real contemporary trip, saved so the demo survives a dead network), bypassing
 * TripForm entirely -- it never fills the form or reads its state. That is deliberate: an
 * earlier version filled the form and inferred the mode from "was demo loaded", which broke
 * the moment someone loaded the demo and then edited a field (still cached_replay, but
 * scoring whatever they'd typed). Two independent paths with no shared state cannot have
 * that bug. Both render through the same PrototypeResultsPage, using the same `score.ts`
 * contract.
 *
 * This button used to be labeled "Load the Hurricane Helene replay" and claimed to replay
 * Helene -- it never did; `cached_replay` has always served a saved *contemporary* trip
 * (real, but dry: NC had no active weather that night). That mismatch is fixed here by
 * relabeling honestly and linking to the real, dedicated Helene case study page
 * (`/case-studies/helene`, `GET /api/v1/demo/helene`) instead of pretending this button
 * shows it. See docs/prototype_score_spec.md's "Historical case study" section for why
 * historical reanalysis must stay off this page's live/cached path entirely.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import TripForm from '@/components/TripForm';
import { ApiError, scoreTrip } from '@/services/api';
import { toEasternIso } from '@/utils/departureTime';
import type { Location, TripRequest } from '@/types/trip';

// A real trip saved by scripts/save_live_trip.py (artifacts/demo/saved_trip_request.json).
// These values are display-only for this button: `mode: 'cached_replay'` makes the
// backend ignore whatever origin/destination/departure is submitted and replay that saved
// trip instead, so keep these in sync with the saved fixture's own origin/destination or
// the heading on the results page will say the wrong place names.
const DEMO_SCENARIO: { origin: Location; destination: Location; departureLocal: string } = {
  origin: { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 },
  destination: { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 },
  departureLocal: '2024-09-27T12:00',
};

export default function PlannerPage() {
  const navigate = useNavigate();
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

  function runSavedDemoTrip() {
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
        and it never overrides an official National Weather Service warning. Submitting a trip below
        scores it live, using the real current forecast and official alerts. For current conditions
        and official warnings, visit weather.gov.
      </p>

      <div className="card" style={{ marginTop: 'var(--space-4)' }}>
        <button
          type="button"
          onClick={runSavedDemoTrip}
          disabled={submitting}
          className="btn"
          style={{ marginBottom: 'var(--space-2)' }}
        >
          Load saved demo trip (offline fallback)
        </button>
        <p className="note" style={{ marginTop: 0, marginBottom: 'var(--space-4)' }}>
          A real trip saved earlier tonight, replayed with no network call, for when the room's
          Wi-Fi drops. Looking for a severe-weather example instead? See the{' '}
          <Link to="/case-studies/helene">Hurricane Helene case study</Link>, a real severe event,
          scored by this same rule.
        </p>

        <TripForm onSubmit={handleFormSubmit} />

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
