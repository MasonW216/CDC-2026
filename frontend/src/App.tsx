/**
 * Application shell and routes.
 *
 * Routes:
 *    /             PlannerPage (sidebar + map, one page: input, the
 *                  prototype hazard index, and the route map together --
 *                  see PlannerPage's own docstring)
 *    /methodology  MethodologyPage   (not yet built -- shows a placeholder)
 *    /about        AboutPage         (not yet built -- shows a placeholder)
 *
 * The header owns branding, primary nav, a place search (sets the planner's
 * origin via HeaderSearchContext), and the light/dark toggle. The full
 * standing safety disclaimer lives on the planner page itself (its own
 * acceptance criterion); this header only names the product.
 */
import { NavLink, Route, Routes } from 'react-router-dom';

import HeaderSearchBar from './components/HeaderSearchBar';
import PivotLogo from './components/PivotLogo';
import ThemeToggle from './components/ThemeToggle';
import { HeaderSearchProvider } from './contexts/HeaderSearchContext';
import PlannerPage from './pages/PlannerPage';

function ComingSoon({ page }: { page: string }) {
  return (
    <p className="note" style={{ padding: 'var(--space-5)' }}>
      The {page} isn't built yet. For current conditions and official warnings, visit weather.gov.
    </p>
  );
}

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? 'active' : '';
}

export default function App() {
  return (
    <HeaderSearchProvider>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <div className="pivot-shell">
        <header className="pivot-header">
          <NavLink to="/" className="pivot-header__brand" aria-label="PIVOT, home">
            <PivotLogo />
          </NavLink>
          <nav aria-label="Primary" className="pivot-header__nav">
            <NavLink to="/" className={navLinkClass} end>
              Plan a trip
            </NavLink>
            <NavLink to="/methodology" className={navLinkClass}>
              Methodology
            </NavLink>
            <NavLink to="/about" className={navLinkClass}>
              About
            </NavLink>
          </nav>
          <div className="pivot-header__actions">
            <HeaderSearchBar />
            <ThemeToggle />
          </div>
        </header>
        <main id="main-content" className="pivot-main">
          <Routes>
            <Route path="/" element={<PlannerPage />} />
            <Route path="/methodology" element={<ComingSoon page="methodology page" />} />
            <Route path="/about" element={<ComingSoon page="about page" />} />
            <Route path="*" element={<ComingSoon page="page" />} />
          </Routes>
        </main>
        <footer className="pivot-footer">
          <p style={{ margin: 0 }}>
            Map and road data &copy; OpenStreetMap contributors. Storm event data from NOAA.
          </p>
        </footer>
      </div>
    </HeaderSearchProvider>
  );
}
