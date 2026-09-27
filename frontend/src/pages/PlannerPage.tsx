/**
 * Trip planner page.
 *
 * Page chrome (heading, safety disclaimer, demo-scenario shortcut) around
 * TripForm, which owns origin/destination search and departure-time input and
 * validation. The disclaimer is visible before the user submits, not after.
 *
 * Submits to POST /api/v1/trips/score. The Hurricane Helene demo button
 * always submits `mode: 'cached_replay'` (a saved, offline-safe response, no
 * live network call); any other trip submits `mode: 'live'` -- real OSRM,
 * Open-Meteo, and NWS calls, per the live routing/scoring path. Both render
 * through the same PrototypeResultsPage, using the same `score.ts` contract.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import TripForm from '@/components/TripForm';
import { ApiError, scoreTrip } from '@/services/api';
import type { Location, TripRequest } from '@/types/trip';

// Mirrors configs/demo.yaml's one non-placeholder scenario. Keep in sync with
// that file; a mismatch here is cosmetic (it only pre-fills the form) but
// should not be allowed to drift indefinitely.
const DEMO_SCENARIO: {
  origin: Location;
  destination: Location;
  departureLocal: string;
} = {
  origin: { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 },
  destination: { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 },
  departureLocal: '2024-09-27T12:00',
};

export default function PlannerPage() {
  const navigate = useNavigate();
  // Bumped on "load demo" to remount TripForm with fresh initial values --
  // simpler and less error-prone than making every field externally
  // controlled just for the one preset button.
  const [demoKey, setDemoKey] = useState(0);
  const [demo, setDemo] = useState<typeof DEMO_SCENARIO | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function loadDemoScenario() {
    setDemo(DEMO_SCENARIO);
    setDemoKey((key) => key + 1);
  }

  async function handleSubmit(request: TripRequest) {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const score = await scoreTrip({ ...request, mode: demo ? 'cached_replay' : 'live' });
      navigate('/results', { state: { score, request } });
    } catch (error) {
      setSubmitError(error instanceof ApiError ? error.message : 'Could not score this trip.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section aria-labelledby="planner-heading">
      <h2 id="planner-heading" className="page-title">
        Plan a trip
      </h2>
      <p role="note" className="note">
        StormRoute compares the modeled weather-hazard exposure of routes and departure times based
        on available weather data. It is a comparative decision index, not a guarantee of safety,
        and it never overrides an official National Weather Service warning. This demo replays
        archived Hurricane Helene conditions with a prototype hazard indicator, not a live forecast.
        For current conditions and official warnings, visit weather.gov.
      </p>

      <div className="card" style={{ marginTop: 'var(--space-4)' }}>
        <button
          type="button"
          onClick={loadDemoScenario}
          className="btn"
          style={{ marginBottom: 'var(--space-4)' }}
        >
          Load the Hurricane Helene replay
        </button>

        <TripForm
          key={demoKey}
          onSubmit={handleSubmit}
          initialOrigin={demo?.origin ?? null}
          initialDestination={demo?.destination ?? null}
          initialDepartureLocal={demo?.departureLocal ?? ''}
        />

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
