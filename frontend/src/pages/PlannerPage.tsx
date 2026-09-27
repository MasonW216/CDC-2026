/**
 * Trip planner page.
 *
 * Origin, destination, departure date and time, an analyze-trip button, and a
 * concise safety disclaimer that is visible before the user submits, not after.
 *
 * There is no geocoding service in the plan (docs/build_guide.md never names
 * one), so origin and destination are a label plus latitude/longitude, filled
 * in by hand or from the one real demo scenario in configs/demo.yaml. #18
 * (the API) and #20 (the results page) do not exist yet, so submitting only
 * records the request and navigates to /results; it does not call anything.
 */
import { useId, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import type { Location, TripRequest } from '@/types/trip';
import { toEasternIso } from '@/utils/departureTime';

// Mirrors configs/demo.yaml's one non-placeholder scenario. Keep in sync with
// that file; a mismatch here is cosmetic (it only pre-fills the form) but
// should not be allowed to drift indefinitely.
const DEMO_SCENARIO = {
  id: 'helene_asheville_charlotte',
  label: 'Hurricane Helene replay — Asheville to Charlotte',
  origin: { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 },
  destination: { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 },
  departureLocal: '2024-09-27T12:00',
} as const;

interface LocationDraft {
  label: string;
  lat: string;
  lon: string;
}

const EMPTY_LOCATION: LocationDraft = { label: '', lat: '', lon: '' };

type Errors = Partial<Record<'origin' | 'destination' | 'departure', string>>;

function parseLocation(
  draft: LocationDraft,
  field: string,
  errors: Errors,
  key: keyof Errors,
): Location | null {
  if (!draft.label.trim()) {
    errors[key] = `Enter a label for the ${field}.`;
    return null;
  }
  const lat = Number(draft.lat);
  const lon = Number(draft.lon);
  if (
    draft.lat.trim() === '' ||
    draft.lon.trim() === '' ||
    Number.isNaN(lat) ||
    Number.isNaN(lon)
  ) {
    errors[key] = `Enter numeric latitude and longitude for the ${field}.`;
    return null;
  }
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
    errors[key] = `Latitude/longitude for the ${field} is out of range.`;
    return null;
  }
  return { label: draft.label.trim(), lat, lon };
}

function LocationFields({
  legend,
  value,
  onChange,
  error,
  idPrefix,
}: {
  legend: string;
  value: LocationDraft;
  onChange: (next: LocationDraft) => void;
  error?: string | undefined;
  idPrefix: string;
}) {
  const errorId = `${idPrefix}-error`;
  return (
    <fieldset>
      <legend>{legend}</legend>
      <div>
        <label htmlFor={`${idPrefix}-label`}>Place name</label>
        <input
          id={`${idPrefix}-label`}
          type="text"
          value={value.label}
          onChange={(event) => onChange({ ...value, label: event.target.value })}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
        />
      </div>
      <div>
        <label htmlFor={`${idPrefix}-lat`}>Latitude</label>
        <input
          id={`${idPrefix}-lat`}
          type="number"
          inputMode="decimal"
          step="any"
          value={value.lat}
          onChange={(event) => onChange({ ...value, lat: event.target.value })}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
        />
      </div>
      <div>
        <label htmlFor={`${idPrefix}-lon`}>Longitude</label>
        <input
          id={`${idPrefix}-lon`}
          type="number"
          inputMode="decimal"
          step="any"
          value={value.lon}
          onChange={(event) => onChange({ ...value, lon: event.target.value })}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
        />
      </div>
      {error ? (
        <p id={errorId} role="alert">
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}

export default function PlannerPage() {
  const navigate = useNavigate();
  const departureId = useId();
  const departureErrorId = `${departureId}-error`;

  const [origin, setOrigin] = useState<LocationDraft>(EMPTY_LOCATION);
  const [destination, setDestination] = useState<LocationDraft>(EMPTY_LOCATION);
  const [departureLocal, setDepartureLocal] = useState('');
  const [errors, setErrors] = useState<Errors>({});

  function loadDemoScenario() {
    setOrigin({
      label: DEMO_SCENARIO.origin.label,
      lat: String(DEMO_SCENARIO.origin.lat),
      lon: String(DEMO_SCENARIO.origin.lon),
    });
    setDestination({
      label: DEMO_SCENARIO.destination.label,
      lat: String(DEMO_SCENARIO.destination.lat),
      lon: String(DEMO_SCENARIO.destination.lon),
    });
    setDepartureLocal(DEMO_SCENARIO.departureLocal);
    setErrors({});
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: Errors = {};
    const originLocation = parseLocation(origin, 'origin', nextErrors, 'origin');
    const destinationLocation = parseLocation(
      destination,
      'destination',
      nextErrors,
      'destination',
    );

    let departureIso: string | null = null;
    if (!departureLocal) {
      nextErrors.departure = 'Choose a departure date and time.';
    } else {
      try {
        departureIso = toEasternIso(departureLocal);
      } catch {
        nextErrors.departure = 'That departure date and time is not valid.';
      }
    }

    setErrors(nextErrors);
    if (
      Object.keys(nextErrors).length > 0 ||
      !originLocation ||
      !destinationLocation ||
      !departureIso
    ) {
      return;
    }

    const request: TripRequest = {
      origin: originLocation,
      destination: destinationLocation,
      departure_time: departureIso,
      mode: 'cached_replay',
    };
    navigate('/results', { state: { request } });
  }

  return (
    <section aria-labelledby="planner-heading">
      <h2 id="planner-heading">Plan a trip</h2>
      <p role="note">
        StormRoute compares the modeled weather-hazard exposure of routes and departure times based
        on available weather data. It is a comparative decision index, not a guarantee of safety,
        and it never overrides an official National Weather Service warning. For current conditions
        and official warnings, visit weather.gov.
      </p>

      <button type="button" onClick={loadDemoScenario}>
        Load the Hurricane Helene replay
      </button>

      <form onSubmit={handleSubmit} noValidate>
        <LocationFields
          legend="Origin"
          value={origin}
          onChange={setOrigin}
          error={errors.origin}
          idPrefix="origin"
        />
        <LocationFields
          legend="Destination"
          value={destination}
          onChange={setDestination}
          error={errors.destination}
          idPrefix="destination"
        />

        <div>
          <label htmlFor={departureId}>Departure date and time (Eastern)</label>
          <input
            id={departureId}
            type="datetime-local"
            value={departureLocal}
            onChange={(event) => setDepartureLocal(event.target.value)}
            aria-invalid={Boolean(errors.departure)}
            aria-describedby={errors.departure ? departureErrorId : undefined}
          />
          {errors.departure ? (
            <p id={departureErrorId} role="alert">
              {errors.departure}
            </p>
          ) : null}
        </div>

        <button type="submit">Analyze trip</button>
      </form>
    </section>
  );
}
