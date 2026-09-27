/**
 * Application shell and routes.
 *
 * Routes:
 *    /             PlannerPage
 *    /results      PrototypeResultsPage (MVP demo: the prototype hazard
 *                  indicator replay, not the real ResultsPage -- see that
 *                  file, milestone 7, for the production Weather Safety Score)
 *    /case-studies/helene  HeleneCaseStudyPage (standalone historical replay,
 *                  GET /api/v1/demo/helene -- never reachable from the planner
 *                  or from a live/cached trip result; see that file and
 *                  docs/prototype_score_spec.md's "Historical case study")
 *    /methodology  MethodologyPage   (not yet built -- shows a placeholder)
 *    /route        LiveRoutePage     (dev preview: a live OSRM path between
 *                  any two points, no hazard assessment -- not part of the
 *                  MVP demo, calls the rate-limited public OSRM server)
 *
 * Also owns the persistent header and map/data source attribution required by
 * the OpenStreetMap and NOAA licenses. The full standing safety disclaimer
 * lives on the planner page itself (its own acceptance criterion); this
 * header only names the product.
 */
import { NavLink, Route, Routes } from 'react-router-dom';

import HeleneCaseStudyPage from './pages/HeleneCaseStudyPage';
import LiveRoutePage from './pages/LiveRoutePage';
import PlannerPage from './pages/PlannerPage';
import PrototypeResultsPage from './pages/PrototypeResultsPage';

function ComingSoon({ page }: { page: string }) {
  return (
    <p className="note">
      The {page} isn't built yet. For current conditions and official warnings, visit weather.gov.
    </p>
  );
}

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? 'active' : '';
}

export default function App() {
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <div className="app-card">
        <header className="topbar">
          <div className="topbar__brand">
            <span className="topbar__brand-icon" aria-hidden="true">
              ⛈
            </span>
            <h1 style={{ margin: 0, fontSize: '1.05rem' }}>StormRoute</h1>
          </div>
          <nav aria-label="Primary" className="topbar__nav">
            <NavLink to="/" className={navLinkClass} end>
              Plan a trip
            </NavLink>
            <NavLink to="/route" className={navLinkClass}>
              Live route (dev)
            </NavLink>
            <NavLink to="/case-studies/helene" className={navLinkClass}>
              Helene case study
            </NavLink>
            <NavLink to="/methodology" className={navLinkClass}>
              Methodology
            </NavLink>
          </nav>
        </header>
        <main id="main-content" className="main-content">
          <Routes>
            <Route path="/" element={<PlannerPage />} />
            <Route path="/results" element={<PrototypeResultsPage />} />
            <Route path="/case-studies/helene" element={<HeleneCaseStudyPage />} />
            <Route path="/route" element={<LiveRoutePage />} />
            <Route path="/methodology" element={<ComingSoon page="methodology page" />} />
            <Route path="*" element={<ComingSoon page="page" />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <p style={{ margin: 0 }}>
            Map and road data &copy; OpenStreetMap contributors. Storm event data from NOAA.
          </p>
        </footer>
      </div>
    </div>
  );
}
