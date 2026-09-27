/**
 * App shell: routing to the planner page, and a placeholder for pages that
 * don't exist yet (#20 results, methodology).
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

  it('shows a placeholder for the results page, not a blank screen', () => {
    renderAt('/results');
    expect(screen.getByText(/isn't built yet/i)).toBeTruthy();
  });

  it('shows a placeholder for an unknown path', () => {
    renderAt('/nonsense');
    expect(screen.getByText(/isn't built yet/i)).toBeTruthy();
  });
});
