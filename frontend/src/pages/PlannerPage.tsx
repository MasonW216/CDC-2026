/**
 * Trip planner page.
 *
 * Page chrome (heading, safety disclaimer, demo-scenario shortcut) around
 * TripForm, which owns origin/destination search and departure-time input and
 * validation. The disclaimer is visible before the user submits, not after.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import TripForm from '@/components/TripForm';
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

  function loadDemoScenario() {
    setDemo(DEMO_SCENARIO);
    setDemoKey((key) => key + 1);
  }

  function handleSubmit(request: TripRequest) {
    navigate('/results', { state: { request } });
  }

  return (
    <section aria-labelledby="planner-heading">
      <h2 id="planner-heading">Plan a trip</h2>
      <p role="note">
        This demo replays archived flood conditions during Hurricane Helene. Its prototype
        indicator is not a live forecast or a guarantee of safety, and it never overrides an
        official National Weather Service warning. For current conditions and official warnings,
        visit weather.gov.
      </p>

      <button type="button" onClick={loadDemoScenario}>
        Load the Hurricane Helene replay
      </button>

      <TripForm
        key={demoKey}
        onSubmit={handleSubmit}
        initialOrigin={demo?.origin ?? null}
        initialDestination={demo?.destination ?? null}
        initialDepartureLocal={demo?.departureLocal ?? ''}
      />
    </section>
  );
}
