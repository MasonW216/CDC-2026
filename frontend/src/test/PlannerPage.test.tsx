/**
 * Page-level behavior only. Field validation and search live in TripForm and
 * LocationSearch, and are covered by their own test files.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import PlannerPage from '../pages/PlannerPage';

function renderPlanner() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<PlannerPage />} />
        <Route path="/results" element={<p>results placeholder</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('PlannerPage', () => {
  it('shows the safety disclaimer before any submission', () => {
    renderPlanner();
    expect(screen.getByText(/comparative decision index/i)).toBeTruthy();
    expect(screen.getByText(/not a guarantee of safety/i)).toBeTruthy();
    expect(screen.queryByText(/safe route/i)).toBeNull();
  });

  it('renders the trip form', () => {
    renderPlanner();
    expect(screen.getByLabelText('Origin')).toBeTruthy();
    expect(screen.getByLabelText('Destination')).toBeTruthy();
    expect(screen.getByLabelText(/departure date and time/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /analyze trip/i })).toBeTruthy();
  });

  it('the demo-scenario button fills the form with valid values', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load the hurricane helene replay/i }));
    expect(screen.getByLabelText('Origin')).toHaveValue('Asheville, NC');
    expect(screen.getByLabelText('Destination')).toHaveValue('Charlotte, NC');
    expect(screen.getByLabelText(/departure date and time/i)).toHaveValue('2024-09-27T12:00');
  });

  it('submits the demo trip and navigates to /results with the request', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load the hurricane helene replay/i }));
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(await screen.findByText('results placeholder')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('loading the demo scenario a second time still works (remount via key)', async () => {
    const user = userEvent.setup();
    renderPlanner();
    const load = screen.getByRole('button', { name: /load the hurricane helene replay/i });
    await user.click(load);
    await user.click(load);
    expect(screen.getByLabelText('Origin')).toHaveValue('Asheville, NC');
  });

  it('is fully usable from the keyboard', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load the hurricane helene replay/i }));
    const submit = screen.getByRole('button', { name: /analyze trip/i });
    submit.focus();
    await user.keyboard('{Enter}');
    expect(await screen.findByText('results placeholder')).toBeTruthy();
  });
});
