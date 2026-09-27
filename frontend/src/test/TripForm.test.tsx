import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import TripForm from '../components/TripForm';
import type { Location } from '../types/trip';

const ASHEVILLE = { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 };
const CHARLOTTE = { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 };
const KNOWN_PLACES: Record<string, Location> = {
  [ASHEVILLE.label]: ASHEVILLE,
  [CHARLOTTE.label]: CHARLOTTE,
};

// A datetime-local string a few days out, so this test file keeps working no
// matter when it's run, without depending on the system clock at write time.
function futureDatetimeLocal(): string {
  const future = new Date(Date.now() + 3 * 24 * 3600 * 1000);
  return future.toISOString().slice(0, 16);
}

vi.mock('../components/LocationSearch', () => ({
  default: ({
    id,
    label,
    onChange,
    error,
  }: {
    id: string;
    label: string;
    onChange: (value: Location | null) => void;
    error?: string;
  }) => (
    <div>
      <label htmlFor={id}>{label}</label>
      <input id={id} onChange={(e) => onChange(KNOWN_PLACES[e.target.value] ?? null)} />
      {error ? <p role="alert">{error}</p> : null}
    </div>
  ),
}));

function setup() {
  const onSubmit = vi.fn();
  render(<TripForm onSubmit={onSubmit} />);
  return { onSubmit, user: userEvent.setup() };
}

async function fillOriginAndDestination(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Origin'), ASHEVILLE.label);
  await user.type(screen.getByLabelText('Destination'), CHARLOTTE.label);
}

describe('TripForm', () => {
  it('has an accessible, keyboard-reachable field for each input', () => {
    setup();
    expect(screen.getByLabelText('Origin')).toBeTruthy();
    expect(screen.getByLabelText('Destination')).toBeTruthy();
    expect(screen.getByLabelText(/departure date and time/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /analyze trip/i })).toBeTruthy();
  });

  it('blocks submission and reports every empty field inline', async () => {
    const { user, onSubmit } = setup();
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getAllByRole('alert').length).toBeGreaterThanOrEqual(3);
  });

  it('submits a well-formed request with a future departure', async () => {
    const { user, onSubmit } = setup();
    await fillOriginAndDestination(user);
    await user.type(screen.getByLabelText(/departure date and time/i), futureDatetimeLocal());
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    const request = onSubmit.mock.calls[0]![0];
    expect(request.origin).toEqual(ASHEVILLE);
    expect(request.destination).toEqual(CHARLOTTE);
    expect(new Date(request.departure_time).getTime()).toBeGreaterThan(Date.now());
  });

  it('rejects an invalid departure value inline', async () => {
    const { user, onSubmit } = setup();
    await fillOriginAndDestination(user);
    const departure = screen.getByLabelText(/departure date and time/i);
    await user.type(departure, '2024-13-99T99:99');
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('rejects a departure in the past inline, before any submit', async () => {
    const { user, onSubmit } = setup();
    await fillOriginAndDestination(user);
    await user.type(screen.getByLabelText(/departure date and time/i), '2020-01-01T00:00');
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/future/i);
  });

  it('accepts a pre-filled value, e.g. for a caller that seeds the form', async () => {
    const { user, onSubmit } = setup();
    const future = futureDatetimeLocal();
    render(
      <TripForm
        onSubmit={onSubmit}
        initialOrigin={ASHEVILLE}
        initialDestination={CHARLOTTE}
        initialDepartureLocal={future}
      />,
    );
    const buttons = screen.getAllByRole('button', { name: /analyze trip/i });
    await user.click(buttons[buttons.length - 1]!);
    expect(onSubmit).toHaveBeenCalledTimes(1);
    const request = onSubmit.mock.calls[0]![0];
    expect(request.origin).toEqual(ASHEVILLE);
    expect(request.destination).toEqual(CHARLOTTE);
  });
});
