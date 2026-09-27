import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import LocationSearch from '../components/LocationSearch';
import * as api from '../services/api';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<typeof api>('../services/api');
  return { ...actual, geocodeSearch: vi.fn(), geocodeReverse: vi.fn() };
});

const ASHEVILLE = { label: 'Asheville, NC, USA', lat: 35.5951, lon: -82.5515, confidence: 0.9 };
const ASHEBORO = { label: 'Asheboro, NC, USA', lat: 35.7079, lon: -79.8136, confidence: 0.6 };

function setup(props: Partial<React.ComponentProps<typeof LocationSearch>> = {}) {
  const onChange = vi.fn();
  render(<LocationSearch id="origin" label="Origin" value={null} onChange={onChange} {...props} />);
  return { onChange, user: userEvent.setup() };
}

beforeEach(() => {
  vi.mocked(api.geocodeSearch).mockReset();
  vi.mocked(api.geocodeReverse).mockReset();
});

describe('LocationSearch', () => {
  it('has an accessible label', () => {
    setup();
    expect(screen.getByLabelText('Origin')).toBeTruthy();
  });

  it('searches after typing at least 3 characters and lists results', async () => {
    vi.mocked(api.geocodeSearch).mockResolvedValue([ASHEVILLE, ASHEBORO]);
    const { user } = setup();
    await user.type(screen.getByLabelText('Origin'), 'Ashe');
    await waitFor(() => expect(api.geocodeSearch).toHaveBeenCalledWith('Ashe'));
    expect(await screen.findByRole('button', { name: /Asheville, NC, USA/ })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Asheboro, NC, USA/ })).toBeTruthy();
  });

  it('does not search below the minimum query length', async () => {
    const { user } = setup();
    await user.type(screen.getByLabelText('Origin'), 'As');
    await new Promise((resolve) => setTimeout(resolve, 350));
    expect(api.geocodeSearch).not.toHaveBeenCalled();
  });

  it('selecting a result calls onChange and fills the field', async () => {
    vi.mocked(api.geocodeSearch).mockResolvedValue([ASHEVILLE]);
    const { user, onChange } = setup();
    await user.type(screen.getByLabelText('Origin'), 'Asheville');
    const option = await screen.findByRole('button', { name: /Asheville, NC, USA/ });
    await user.click(option);
    expect(onChange).toHaveBeenCalledWith({
      label: 'Asheville, NC, USA',
      lat: 35.5951,
      lon: -82.5515,
    });
    expect(screen.getByLabelText('Origin')).toHaveValue('Asheville, NC, USA');
    expect(screen.queryByRole('button', { name: /Asheville, NC, USA/ })).toBeNull();
  });

  it('editing the text after a selection clears the resolved value', async () => {
    vi.mocked(api.geocodeSearch).mockResolvedValue([]);
    const { user, onChange } = setup({ value: ASHEVILLE });
    await user.type(screen.getByLabelText('Origin'), 'x');
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it('shows a message when there are no matches', async () => {
    vi.mocked(api.geocodeSearch).mockResolvedValue([]);
    const { user } = setup();
    await user.type(screen.getByLabelText('Origin'), 'zzzzznotaplace');
    expect(await screen.findByText(/no matches/i)).toBeTruthy();
  });

  it('shows an inline error when the search fails, without crashing', async () => {
    vi.mocked(api.geocodeSearch).mockRejectedValue(new api.ApiError('boom', 502));
    const { user } = setup();
    await user.type(screen.getByLabelText('Origin'), 'Asheville');
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn.t search/i);
  });

  it('only applies the latest search when responses arrive out of order', async () => {
    let resolveFirst!: (v: api.GeocodeResult[]) => void;
    vi.mocked(api.geocodeSearch).mockImplementationOnce(
      () => new Promise((resolve) => (resolveFirst = resolve)),
    );
    vi.mocked(api.geocodeSearch).mockResolvedValueOnce([ASHEBORO]);
    const { user } = setup();
    const input = screen.getByLabelText('Origin');
    await user.type(input, 'Ash');
    await waitFor(() => expect(api.geocodeSearch).toHaveBeenCalledTimes(1)); // first debounce fired
    await user.type(input, 'ebor');
    await screen.findByRole('button', { name: /Asheboro/ });
    resolveFirst([ASHEVILLE]);
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.queryByRole('button', { name: /Asheville, NC, USA/ })).toBeNull();
  });

  it('offers "Use my location" only when allowCurrentLocation is set', () => {
    setup({ allowCurrentLocation: true });
    expect(screen.getByRole('button', { name: /use my location/i })).toBeTruthy();
  });

  it('resolves the current location via the browser and reverse geocoding', async () => {
    vi.mocked(api.geocodeReverse).mockResolvedValue([ASHEVILLE]);
    const getCurrentPosition = vi.fn((success: PositionCallback) =>
      success({ coords: { latitude: 35.5951, longitude: -82.5515 } } as GeolocationPosition),
    );
    vi.stubGlobal('navigator', { ...navigator, geolocation: { getCurrentPosition } });
    const { user, onChange } = setup({ allowCurrentLocation: true });
    await user.click(screen.getByRole('button', { name: /use my location/i }));
    await waitFor(() =>
      expect(onChange).toHaveBeenCalledWith(
        ASHEVILLE.label
          ? { label: ASHEVILLE.label, lat: ASHEVILLE.lat, lon: ASHEVILLE.lon }
          : undefined,
      ),
    );
  });

  it('shows an inline error when geolocation is denied', async () => {
    const getCurrentPosition = vi.fn((_success: PositionCallback, error: PositionErrorCallback) =>
      error({ code: 1, message: 'denied' } as GeolocationPositionError),
    );
    vi.stubGlobal('navigator', { ...navigator, geolocation: { getCurrentPosition } });
    const { user } = setup({ allowCurrentLocation: true });
    await user.click(screen.getByRole('button', { name: /use my location/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/location/i);
  });

  it('shows an inline error when the browser has no geolocation support', async () => {
    vi.stubGlobal('navigator', { ...navigator, geolocation: undefined });
    const { user } = setup({ allowCurrentLocation: true });
    await user.click(screen.getByRole('button', { name: /use my location/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/not supported/i);
  });
});
