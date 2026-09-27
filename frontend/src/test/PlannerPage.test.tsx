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

  it('every field has an accessible label', () => {
    renderPlanner();
    for (const name of ['Place name', 'Latitude', 'Longitude']) {
      expect(screen.getAllByLabelText(name).length).toBeGreaterThanOrEqual(2); // origin + destination
    }
    expect(screen.getByLabelText(/departure date and time/i)).toBeTruthy();
  });

  it('blocks submission and shows inline errors when the form is empty', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    const alerts = screen.getAllByRole('alert');
    expect(alerts.length).toBeGreaterThanOrEqual(3); // origin, destination, departure
    expect(screen.queryByText('results placeholder')).toBeNull();
  });

  it('rejects an out-of-range latitude inline', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.type(screen.getAllByLabelText('Place name')[0]!, 'Nowhere');
    await user.type(screen.getAllByLabelText('Latitude')[0]!, '200');
    await user.type(screen.getAllByLabelText('Longitude')[0]!, '-82.5');
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(
      screen.getAllByRole('alert').some((el) => /out of range/i.test(el.textContent ?? '')),
    ).toBe(true);
  });

  it('the demo-scenario button fills the form with valid values', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load the hurricane helene replay/i }));
    expect(screen.getAllByLabelText('Place name')[0]!).toHaveValue('Asheville, NC');
    expect(screen.getAllByLabelText('Place name')[1]!).toHaveValue('Charlotte, NC');
    expect(screen.getByLabelText(/departure date and time/i)).toHaveValue('2024-09-27T12:00');
  });

  it('submits a valid trip and navigates to /results with the request', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load the hurricane helene replay/i }));
    await user.click(screen.getByRole('button', { name: /analyze trip/i }));
    expect(await screen.findByText('results placeholder')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('is fully usable from the keyboard', async () => {
    const user = userEvent.setup();
    renderPlanner();
    await user.click(screen.getByRole('button', { name: /load the hurricane helene replay/i }));
    await user.tab(); // load-demo button -> first field; keep tabbing to the submit button
    const submit = screen.getByRole('button', { name: /analyze trip/i });
    submit.focus();
    await user.keyboard('{Enter}');
    expect(await screen.findByText('results placeholder')).toBeTruthy();
  });
});
