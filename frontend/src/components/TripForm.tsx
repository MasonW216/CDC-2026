/**
 * Origin, destination, and departure-time input.
 *
 * Fully keyboard navigable, with labeled inputs, inline validation, and errors
 * announced to assistive technology (role="alert"). Origin and destination are
 * resolved places (LocationSearch), not raw text, so the request this builds
 * always carries real coordinates.
 *
 * Departure time is read as North Carolina wall-clock time and converted to
 * ISO 8601 with the correct offset (utils/departureTime). Rejects a departure
 * time in the past client-side, mirroring POST /api/v1/trips/score's own 422
 * rule, so the error shows before a network round trip. (The Hurricane
 * Helene demo replay bypasses this component entirely -- see PlannerPage --
 * so its real 2024 departure is never run through this check.)
 *
 * Does not navigate or call the API itself; the caller supplies `onSubmit`.
 */
import { useId, useState } from 'react';

import type { Location, TripRequest } from '@/types/trip';
import { toEasternIso } from '@/utils/departureTime';
import LocationSearch from './LocationSearch';

type Errors = Partial<Record<'origin' | 'destination' | 'departure', string>>;

interface TripFormProps {
  onSubmit: (request: TripRequest) => void;
  initialOrigin?: Location | null;
  initialDestination?: Location | null;
  initialDepartureLocal?: string;
}

export default function TripForm({
  onSubmit,
  initialOrigin = null,
  initialDestination = null,
  initialDepartureLocal = '',
}: TripFormProps) {
  const departureId = useId();
  const departureErrorId = `${departureId}-error`;

  const [origin, setOrigin] = useState<Location | null>(initialOrigin);
  const [destination, setDestination] = useState<Location | null>(initialDestination);
  const [departureLocal, setDepartureLocal] = useState(initialDepartureLocal);
  const [errors, setErrors] = useState<Errors>({});

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: Errors = {};
    if (!origin) nextErrors.origin = 'Search for and select a starting point.';
    if (!destination) nextErrors.destination = 'Search for and select a destination.';

    let departureIso: string | null = null;
    if (!departureLocal) {
      nextErrors.departure = 'Choose a departure date and time.';
    } else {
      try {
        departureIso = toEasternIso(departureLocal);
        if (new Date(departureIso).getTime() <= Date.now()) {
          nextErrors.departure = 'Departure must be in the future.';
          departureIso = null;
        }
      } catch {
        nextErrors.departure = 'That departure date and time is not valid.';
      }
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0 || !origin || !destination || !departureIso) {
      return;
    }
    onSubmit({ origin, destination, departure_time: departureIso });
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <LocationSearch
        id="origin"
        label="Origin"
        value={origin}
        onChange={setOrigin}
        error={errors.origin}
        allowCurrentLocation
      />
      <LocationSearch
        id="destination"
        label="Destination"
        value={destination}
        onChange={setDestination}
        error={errors.destination}
      />

      <div className="field">
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

      <button type="submit" className="btn btn-primary">
        Analyze trip
      </button>
    </form>
  );
}
