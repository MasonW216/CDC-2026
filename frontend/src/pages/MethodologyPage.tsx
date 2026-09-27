/**
 * Methodology page.
 *
 * Describes the rule that is actually implemented and running behind the planner and
 * the Helene case study today (`prototype-score/1`, docs/prototype_score_spec.md) --
 * not the eventual, not-yet-built Weather Safety Score model (docs/risk_methodology.md,
 * Milestone 5). Keeping those two separate on this page, and labeling the second one
 * "planned," is deliberate: this is the page a judge reads to decide whether to trust
 * the rest of the site, so every claim on it must trace to a real source or be marked
 * as not built yet (see responsible_ai.md's claim audit).
 *
 * Every number here (the rain thresholds, alert floors, tie margin, band cutoffs)
 * matches configs/scoring.yaml and docs/prototype_score_spec.md; change all three
 * together if the rule changes.
 */
const ALERT_FLOORS: { event: string; floor: number }[] = [
  { event: 'Flood Watch / Flash Flood Watch', floor: 35 },
  { event: 'Flood Advisory', floor: 50 },
  { event: 'Flood Warning / Flash Flood Warning', floor: 80 },
  { event: 'Flash Flood Emergency', floor: 98 },
];

const BANDS: { range: string; band: string; levelClass: string }[] = [
  { range: '0–24', band: 'Lower concern', levelClass: 'level-badge--0' },
  { range: '25–49', band: 'Elevated concern', levelClass: 'level-badge--1' },
  { range: '50–79', band: 'High concern', levelClass: 'level-badge--2' },
  { range: '80–100', band: 'Severe concern', levelClass: 'level-badge--3' },
];

const SAFETY_STATEMENTS: string[] = [
  'No reported event does not prove safe road conditions. Absence of a report is absence of a report, not a clean bill of health.',
  'County resolution cannot identify whether a particular road is flooded.',
  'This index is a comparative weather-hazard exposure measure. It is not a crash, injury, or fatality predictor.',
  'Recommendations never override a road closure, evacuation order, or National Weather Service warning. Official guidance is shown above any recommendation.',
];

const LIMITATIONS: string[] = [
  'Forecasts are uncertain and can be wrong.',
  'The index does not know about road closures, drainage, or terrain.',
  'A missing alert is not a guarantee that none exists; alerts issued after departure are not seen.',
  'One forecast point represents an entire county.',
  'This is a team-defined comparison rule, not a calibrated flood probability.',
];

export default function MethodologyPage() {
  return (
    <section aria-labelledby="methodology-heading" className="content-page">
      <h2 id="methodology-heading" className="page-title">
        Methodology
      </h2>
      <p className="note">
        What the prototype hazard index compares, what it is built from, and what it deliberately
        does not claim.
      </p>

      <h3 className="section-title" style={{ marginTop: 'var(--space-5)' }}>
        What the index is, and is not
      </h3>
      <p>
        The prototype hazard index is a 0–100 <strong>comparative decision index</strong> for
        judging route options under the same rule and the same weather data. Higher means more
        indicated weather concern. It is a team policy, not a learned or validated quantity: it is
        not a probability of road flooding, and no band is ever called &ldquo;safe.&rdquo;
      </p>
      <div className="card-grid">
        {SAFETY_STATEMENTS.map((statement) => (
          <div key={statement} className="card">
            <p style={{ margin: 0 }}>{statement}</p>
          </div>
        ))}
      </div>

      <h3 className="section-title">Inputs and sources</h3>
      <table className="timeline">
        <thead>
          <tr>
            <th scope="col">Input</th>
            <th scope="col">Source</th>
            <th scope="col">What it measures</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Peak hourly rainfall</td>
            <td>Open-Meteo forecast API</td>
            <td>Highest hourly precipitation over the hours a route stretch overlaps</td>
          </tr>
          <tr>
            <td>Prior 24-hour rainfall</td>
            <td>Open-Meteo forecast API</td>
            <td>Accumulated precipitation over the 24 hours ending at that stretch</td>
          </tr>
          <tr>
            <td>Official flood alerts</td>
            <td>National Weather Service, api.weather.gov</td>
            <td>Active flood products for the county at the time of arrival</td>
          </tr>
        </tbody>
      </table>
      <p className="note">
        A stretch is <strong>assessed</strong> only when forecast hours cover it and the 24 hours
        before it; otherwise its index is left unassessed, never shown as zero. A route where any
        stretch is unassessed reports its index as a lower bound, and the comparison between routes
        becomes unavailable rather than guessed at.
      </p>

      <h3 className="section-title">How a route&rsquo;s index is set</h3>
      <p>
        Each county stretch takes the higher of two components: rainfall intensity, and the highest
        official alert covering it. A route&rsquo;s index is the single highest stretch along it
        &mdash; one severe county sets the whole route&rsquo;s number, even if every other stretch
        is calm.
      </p>
      <p className="note">
        Worked example: peak rain 5&nbsp;mm/h, 30&nbsp;mm over the prior 24 hours, and an active
        Flood Watch. Rainfall alone would score 30; the Flood Watch floor of 35 is higher, so the
        alert &mdash; not the rain &mdash; sets this stretch&rsquo;s index at 35. An alert can only
        raise a stretch&rsquo;s index, never lower it.
      </p>
      <table className="timeline">
        <thead>
          <tr>
            <th scope="col">Official product</th>
            <th scope="col">Index floor</th>
          </tr>
        </thead>
        <tbody>
          {ALERT_FLOORS.map((row) => (
            <tr key={row.event}>
              <td>{row.event}</td>
              <td>{row.floor}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 className="section-title">Bands</h3>
      <ul className="factor-chips" style={{ listStyle: 'none', padding: 0 }}>
        {BANDS.map((row) => (
          <li key={row.band} className="factor-chip">
            <span className={`level-badge ${row.levelClass}`}>{row.band}</span>
            <span className="note" style={{ margin: 0 }}>
              {row.range}
            </span>
          </li>
        ))}
      </ul>

      <h3 className="section-title">Comparing routes</h3>
      <p>
        Two routes within 5 points of each other are called a <strong>tie</strong>: the app will not
        name a lower-concern option when the difference isn&rsquo;t meaningful. A difference of 5
        points or more names the lower-concern route, its added travel time against the fastest
        option, and the size of the gap. If every route shown is 80 or above, the app says so
        regardless of ranking &mdash; there is no lower-concern option to recommend.
      </p>

      <h3 className="section-title">Known limits</h3>
      <ul className="note">
        {LIMITATIONS.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>

      <div className="card" style={{ marginTop: 'var(--space-5)' }}>
        <h3 className="section-title" style={{ marginTop: 0 }}>
          Planned: the Weather Safety Score
        </h3>
        <p style={{ marginBottom: 0 }}>
          A calibrated model &mdash; estimating the probability of a qualifying flood report in a
          county and six-hour window, then combining it across a route&rsquo;s exposure &mdash; is
          designed but <strong>not yet built or evaluated</strong> (build guide, Milestone 5). The
          index shown throughout this site today is the rule described above, not that model. This
          page will be updated, with real evaluation numbers, if and when that model ships.
        </p>
      </div>
    </section>
  );
}
