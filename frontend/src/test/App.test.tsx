/**
 * Scaffold smoke test: the placeholder shell renders inside the router.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import App from '../App';

describe('App placeholder', () => {
  it('renders the StormRoute heading and the build-status note', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByRole('heading', { level: 1, name: 'StormRoute' })).toBeTruthy();
    expect(screen.getByText(/EDA is the first scientific milestone/i)).toBeTruthy();
  });
});
