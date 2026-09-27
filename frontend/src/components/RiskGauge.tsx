/**
 * Circular gauge for the prototype hazard index (0-100).
 *
 * Color always carries the band text underneath it too -- never color alone,
 * per the risk-palette rule in styles.css. `band` drives both the color and
 * the label, so they can never say two different things.
 */
const BAND_LEVEL: Record<string, 0 | 1 | 2 | 3 | 'none'> = {
  'Lower concern': 0,
  'Elevated concern': 1,
  'High concern': 2,
  'Severe concern': 3,
  'Not assessed': 'none',
};

const SIZE = 168;
const STROKE = 14;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

interface RiskGaugeProps {
  index: number | null;
  band: string;
}

export default function RiskGauge({ index, band }: RiskGaugeProps) {
  const level = BAND_LEVEL[band] ?? 'none';
  const value = index ?? 0;
  const progress = Math.max(0, Math.min(100, value)) / 100;
  const dashOffset = CIRCUMFERENCE * (1 - progress);

  return (
    <div
      className="risk-gauge"
      role="img"
      aria-label={`Prototype hazard index: ${index ?? 'not assessed'} of 100, ${band}`}
    >
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} aria-hidden="true">
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={STROKE}
        />
        {index !== null && (
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={`var(--level-${level}-fg)`}
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
          />
        )}
      </svg>
      <div className="risk-gauge__center">
        <span className="risk-gauge__value">{index ?? '–'}</span>
        <span className="risk-gauge__band" style={{ color: `var(--level-${level}-fg)` }}>
          {band}
        </span>
      </div>
    </div>
  );
}
