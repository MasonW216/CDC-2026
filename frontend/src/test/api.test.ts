import { ApiError, geocodeReverse, geocodeSearch } from '../services/api';

function mockFetchOnce(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(body),
    }),
  );
}

describe('geocodeSearch', () => {
  it('requests the search endpoint with the typed text', async () => {
    mockFetchOnce(200, {
      results: [{ label: 'Asheville, NC', lat: 35.6, lon: -82.6, confidence: 1 }],
    });
    const results = await geocodeSearch('Asheville');
    expect(results).toEqual([{ label: 'Asheville, NC', lat: 35.6, lon: -82.6, confidence: 1 }]);
    const [url] = vi.mocked(fetch).mock.calls[0]!;
    expect(String(url)).toContain('/api/v1/geocode/search');
    expect(String(url)).toContain('text=Asheville');
  });

  it('returns an empty array for no matches, not an error', async () => {
    mockFetchOnce(200, { results: [] });
    expect(await geocodeSearch('zzzzz not a place')).toEqual([]);
  });

  it('throws ApiError with the status on a non-2xx response', async () => {
    mockFetchOnce(503, { detail: 'Geocoding is not configured: set ORS_API_KEY in .env.' });
    await expect(geocodeSearch('Asheville')).rejects.toMatchObject({
      status: 503,
      message: expect.stringContaining('ORS_API_KEY'),
    });
  });

  it('is an instance of ApiError', async () => {
    mockFetchOnce(502, { detail: 'geocoding provider returned HTTP 401' });
    await expect(geocodeSearch('Asheville')).rejects.toBeInstanceOf(ApiError);
  });

  it('wraps a network failure as an ApiError', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(geocodeSearch('Asheville')).rejects.toBeInstanceOf(ApiError);
  });
});

describe('geocodeReverse', () => {
  it('requests the reverse endpoint with lat/lon', async () => {
    mockFetchOnce(200, {
      results: [{ label: 'Asheville, NC', lat: 35.5951, lon: -82.5515, confidence: 1 }],
    });
    const results = await geocodeReverse(35.5951, -82.5515);
    expect(results[0]!.label).toBe('Asheville, NC');
    const [url] = vi.mocked(fetch).mock.calls[0]!;
    expect(String(url)).toContain('lat=35.5951');
    expect(String(url)).toContain('lon=-82.5515');
  });
});
