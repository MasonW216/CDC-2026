/**
 * App shell: branding, routing to the planner, methodology, and about pages,
 * and a placeholder for any unknown path.
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
  it('renders the PIVOT brand and the planner page at /', () => {
    renderAt('/');
    expect(screen.getByLabelText(/pivot, home/i)).toBeTruthy();
    expect(screen.getByText('PIVOT')).toBeTruthy();
    expect(screen.getByLabelText('Origin')).toBeTruthy();
  });

  it('renders the methodology page', () => {
    renderAt('/methodology');
    expect(screen.getByRole('heading', { name: 'Methodology' })).toBeTruthy();
  });

  it('renders the about page', () => {
    renderAt('/about');
    expect(screen.getByRole('heading', { name: /about pivot/i })).toBeTruthy();
  });

  it('shows a placeholder for an unknown path', () => {
    renderAt('/nonsense');
    expect(screen.getByText(/isn't built yet/i)).toBeTruthy();
  });
});
