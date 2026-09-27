/**
 * App shell: routing to the planner page, the MVP prototype results screen,
 * and a placeholder for pages that don't exist yet (methodology).
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import App from '../App';

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/*" element={<App />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('App shell', () => {
  it('renders the StormRoute heading and the planner page at /', () => {
    renderAt('/');
    expect(screen.getByRole('heading', { level: 1, name: 'StormRoute' })).toBeTruthy();
    expect(screen.getByRole('heading', { level: 2, name: 'Plan a trip' })).toBeTruthy();
  });

  it('renders the MVP prototype results screen at /results, not a placeholder', () => {
    renderAt('/results');
    expect(screen.queryByText(/isn't built yet/i)).toBeNull();
    expect(screen.getByRole('heading', { level: 2, name: /Asheville.*Charlotte/i })).toBeTruthy();
  });

  it('shows a placeholder for an unknown path', () => {
    renderAt('/nonsense');
    expect(screen.getByText(/isn't built yet/i)).toBeTruthy();
  });
});
