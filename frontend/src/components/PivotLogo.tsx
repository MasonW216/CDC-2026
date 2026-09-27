/**
 * PIVOT wordmark: a flowing arrow (the "pivot" in a route) resolving into a
 * contour/topographic mark (the terrain a route crosses), plus the wordmark.
 * An original approximation of the brand reference, not a traced asset.
 */
export default function PivotLogo({ height = 28 }: { height?: number }) {
  return (
    <span className="pivot-logo" style={{ height }}>
      <svg
        viewBox="0 0 44 40"
        width={height * 1.1}
        height={height}
        aria-hidden="true"
        focusable="false"
      >
        <path
          d="M4 34 C4 34 4 22 4 16 C4 8 10 4 16 4 C22 4 26 8 26 4"
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="4.5"
          strokeLinecap="round"
        />
        <path d="M22 2 L30 4.5 L22.5 9 Z" fill="var(--color-primary)" />
        <circle cx="4" cy="34" r="4" fill="var(--color-primary)" />
        <g fill="none" stroke="var(--color-text)" strokeWidth="1.6">
          <ellipse cx="27" cy="26" rx="13" ry="11" transform="rotate(-18 27 26)" />
          <ellipse cx="27" cy="26" rx="9" ry="7.5" transform="rotate(-18 27 26)" />
          <ellipse cx="27" cy="26" rx="5" ry="4" transform="rotate(-18 27 26)" />
        </g>
        <ellipse
          cx="26"
          cy="27"
          rx="2.4"
          ry="2"
          transform="rotate(-18 26 27)"
          fill="var(--color-text)"
        />
      </svg>
      <span className="pivot-logo__word">PIVOT</span>
    </span>
  );
}
