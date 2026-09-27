/**
 * Application shell and routes.
 *
 * Routes:
 *    /             PlannerPage
 *    /results      ResultsPage
 *    /methodology  MethodologyPage
 *
 * Also owns the persistent header, the source attribution required by the
 * OpenStreetMap and NOAA licenses, and the standing safety disclaimer.
 *
 * TODO(milestone-7): implement. See docs/build_guide.md.
 * Until then this renders a scaffold placeholder so `make web` shows a page.
 */

export default function App() {
  return (
    <main>
      <h1>StormRoute</h1>
      <p>
        The website is under construction. EDA is the first scientific milestone; no scores are
        shown until the model is built and evaluated.
      </p>
      <p>For current conditions and official warnings, visit weather.gov.</p>
    </main>
  );
}
