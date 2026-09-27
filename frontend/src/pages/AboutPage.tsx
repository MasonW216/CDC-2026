/**
 * About page: what PIVOT is, who built it, and the boundaries it holds to.
 *
 * Team roles and the "not intended for" list are drawn from docs/responsible_ai.md
 * (the intended-use section and the six required safety statements) -- kept as roles,
 * not invented names, for teammates not already named in that document.
 */
const NOT_INTENDED_FOR: string[] = [
  'Deciding whether a specific road is passable right now',
  'Predicting crashes, injuries, or deaths',
  'Emergency response, dispatch, or evacuation routing',
  'Autonomous navigation',
  'Any use outside North Carolina',
];

export default function AboutPage() {
  return (
    <section aria-labelledby="about-heading" className="content-page">
      <h2 id="about-heading" className="page-title">
        About PIVOT
      </h2>
      <p className="note">
        A Carolina Data Challenge 2026 entry, Natural Science track: AI for Social Good.
      </p>

      <h3 className="section-title" style={{ marginTop: 'var(--space-5)' }}>
        What this is
      </h3>
      <p>
        PIVOT (built under the working name StormRoute) helps a traveler in North Carolina{' '}
        <strong>compare</strong> routes and departure times by modeled weather-hazard exposure,
        based on available weather data, before they leave. It surfaces which stretch of a route
        carries the most modeled concern and, where the data supports it, what changing the route or
        the departure time would cost in extra minutes.
      </p>
      <p>
        It is a decision-support prototype, not an authority. Official National Weather Service
        alerts are always shown above the model&rsquo;s own read, and can only raise a route&rsquo;s
        concern &mdash; never lower it. See <a href="/methodology">methodology</a> for exactly how
        the index is built, or the <a href="/case-studies/helene">Hurricane Helene disaster demo</a>{' '}
        for what it reports on a real, severe storm.
      </p>

      <h3 className="section-title">Not intended for</h3>
      <ul className="note">
        {NOT_INTENDED_FOR.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h3 className="section-title">The team</h3>
      <div className="card-grid">
        <div className="card">
          <h4 className="subsection-title" style={{ marginTop: 0 }}>
            Product &amp; AI
          </h4>
          <p className="note" style={{ margin: 0 }}>
            Mason &mdash; scope, the scoring rule, and the model roadmap.
          </p>
        </div>
        <div className="card">
          <h4 className="subsection-title" style={{ marginTop: 0 }}>
            Geospatial &amp; website
          </h4>
          <p className="note" style={{ margin: 0 }}>
            Routing, the map, and everything you&rsquo;re using right now.
          </p>
        </div>
        <div className="card">
          <h4 className="subsection-title" style={{ marginTop: 0 }}>
            Evaluation &amp; impact
          </h4>
          <p className="note" style={{ margin: 0 }}>
            Cameron &mdash; the statistics, the claim audit, and holding the rest of us to real
            numbers.
          </p>
        </div>
      </div>

      <h3 className="section-title">Data</h3>
      <p className="note">
        NOAA Storm Events for historical calibration, Open-Meteo for forecast rainfall, National
        Weather Service active alerts, US Census TIGER/Line county boundaries, and OpenStreetMap
        road geometry via OSRM. The <a href="/case-studies/helene">Helene disaster demo</a> instead
        uses ERA5 reanalysis rainfall and archived NWS alerts, clearly separated from any live
        result.
      </p>
    </section>
  );
}
