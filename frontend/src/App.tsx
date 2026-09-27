/**
 * Application shell and routes.
 *
 * Routes:
 *    /             PlannerPage
 *    /results      PrototypeResultsPage (MVP demo: the prototype hazard
 *                  indicator replay, not the real ResultsPage -- see that
 *                  file, milestone 7, for the production Weather Safety Score)
 *    /methodology  MethodologyPage   (not yet built -- shows a placeholder)
 *
 * Also owns the persistent header and map/data source attribution required by
 * the OpenStreetMap and NOAA licenses. The full standing safety disclaimer
 * lives on the planner page itself (its own acceptance criterion); this
 * header only names the product.
 */
import { NavLink, Route, Routes } from 'react-router-dom';

import PlannerPage from './pages/PlannerPage';
import PrototypeResultsPage from './pages/PrototypeResultsPage';

function ComingSoon({ page }: { page: string }) {
  return (
    <p>
      The {page} isn't built yet. For current conditions and official warnings, visit weather.gov.
    </p>
  );
}

export default function App() {
  return (
    <>
      <a href="#main-content">Skip to main content</a>
      <header>
        <h1>StormRoute</h1>
        <nav aria-label="Primary">
          <NavLink to="/">Plan a trip</NavLink>
          <NavLink to="/methodology">Methodology</NavLink>
        </nav>
      </header>
      <main id="main-content">
        <Routes>
          <Route path="/" element={<PlannerPage />} />
          <Route path="/results" element={<PrototypeResultsPage />} />
          <Route path="/methodology" element={<ComingSoon page="methodology page" />} />
          <Route path="*" element={<ComingSoon page="page" />} />
        </Routes>
      </main>
      <footer>
        <p>Map and road data &copy; OpenStreetMap contributors. Storm event data from NOAA.</p>
      </footer>
    </>
  );
}
