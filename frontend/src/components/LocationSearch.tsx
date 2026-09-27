/**
 * A labeled place-search field: type a name, pick a result, or (for the
 * origin) use the browser's own location.
 *
 * Search is debounced and goes through the backend's ORS proxy
 * (services/api.ts), never straight to a third party -- so no key reaches
 * the browser and a provider error surfaces as a normal, readable message
 * instead of an opaque network failure.
 *
 * `value` is the resolved selection (or null): typing without picking a
 * result, or picking one then editing the text again, clears it, so the
 * form can never submit an unresolved place.
 */
import { useEffect, useId, useRef, useState } from 'react';

import type { Location } from '@/types/trip';
import { geocodeReverse, geocodeSearch, type GeocodeResult } from '@/services/api';

const MIN_QUERY_LENGTH = 3;
const DEBOUNCE_MS = 300;

function toLocation(result: GeocodeResult): Location {
  return { label: result.label, lat: result.lat, lon: result.lon };
}

interface LocationSearchProps {
  id: string;
  label: string;
  value: Location | null;
  onChange: (value: Location | null) => void;
  error?: string | undefined;
  allowCurrentLocation?: boolean;
}

export default function LocationSearch({
  id,
  label,
  value,
  onChange,
  error,
  allowCurrentLocation,
}: LocationSearchProps) {
  const [query, setQuery] = useState(value?.label ?? '');
  const [results, setResults] = useState<GeocodeResult[] | null>(null);
  const [status, setStatus] = useState<'idle' | 'searching' | 'locating'>('idle');
  const [searchError, setSearchError] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const requestId = useRef(0);
  const resultsId = useId();
  const errorId = `${id}-error`;
  const statusId = `${id}-status`;

  // A selection made elsewhere (the demo-scenario button, "use my location")
  // should replace whatever is in the field; our own selections already match.
  useEffect(() => {
    setQuery(value?.label ?? '');
  }, [value]);

  useEffect(() => () => clearTimeout(debounceRef.current), []);

  function handleInput(text: string) {
    setQuery(text);
    setLocationError(null);
    if (value) onChange(null);
    clearTimeout(debounceRef.current);
    if (text.trim().length < MIN_QUERY_LENGTH) {
      setResults(null);
      setStatus('idle');
      return;
    }
    const thisRequest = ++requestId.current;
    debounceRef.current = setTimeout(() => {
      setStatus('searching');
      setSearchError(null);
      geocodeSearch(text)
        .then((found) => {
          if (requestId.current !== thisRequest) return; // a newer search has since started
          setResults(found);
          setStatus('idle');
        })
        .catch(() => {
          if (requestId.current !== thisRequest) return;
          setSearchError("Couldn't search for places right now. Try again in a moment.");
          setResults(null);
          setStatus('idle');
        });
    }, DEBOUNCE_MS);
  }

  function pick(result: GeocodeResult) {
    clearTimeout(debounceRef.current);
    requestId.current += 1; // ignore any search still in flight for the old text
    setQuery(result.label); // set directly; don't wait for `value` to round-trip back in
    onChange(toLocation(result));
    setResults(null);
    setStatus('idle');
  }

  function useMyLocation() {
    setLocationError(null);
    if (!navigator.geolocation) {
      setLocationError('Locating is not supported by this browser.');
      return;
    }
    setStatus('locating');
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        geocodeReverse(latitude, longitude)
          .then((found) => {
            const resolved = found[0]
              ? toLocation(found[0])
              : {
                  label: `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`,
                  lat: latitude,
                  lon: longitude,
                };
            onChange(resolved);
            setStatus('idle');
          })
          .catch(() => {
            onChange({
              label: `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`,
              lat: latitude,
              lon: longitude,
            });
            setStatus('idle');
          });
      },
      (geoError) => {
        setStatus('idle');
        setLocationError(
          geoError.code === geoError.PERMISSION_DENIED
            ? 'Location access was denied. Type a starting point instead.'
            : 'Could not get your location. Type a starting point instead.',
        );
      },
    );
  }

  const showResults = results !== null && results.length > 0;
  const showNoMatches = results !== null && results.length === 0 && !searchError;

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="text"
        value={query}
        onChange={(event) => handleInput(event.target.value)}
        autoComplete="off"
        aria-invalid={Boolean(error)}
        aria-describedby={[error ? errorId : null, statusId].filter(Boolean).join(' ')}
      />
      {allowCurrentLocation ? (
        <button
          type="button"
          onClick={useMyLocation}
          disabled={status === 'locating'}
          className="btn"
          style={{ marginTop: 'var(--space-1)' }}
        >
          {status === 'locating' ? 'Locating…' : 'Use my location'}
        </button>
      ) : null}

      <p id={statusId} aria-live="polite" className="field__status">
        {status === 'searching' ? 'Searching…' : null}
        {showNoMatches ? 'No matches found.' : null}
      </p>
      {searchError ? <p role="alert">{searchError}</p> : null}
      {locationError ? <p role="alert">{locationError}</p> : null}
      {showResults ? (
        <ul id={resultsId} className="field__results">
          {results.map((result) => (
            <li key={`${result.lat},${result.lon}`}>
              <button type="button" onClick={() => pick(result)}>
                {result.label}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {error ? (
        <p id={errorId} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
