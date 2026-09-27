/**
 * PIVOT wordmark: the real brand icon (assets/pivot-icon.png, a flowing
 * arrow -- the "pivot" in a route -- resolving into a contour/topographic
 * mark) plus the wordmark text, which stays live text (not part of the
 * image) so it inherits --color-text and reads correctly in both themes.
 * The icon itself is color-locked (blue on transparent) and unaffected by
 * theme, matching the reference brand asset in both light and dark mode.
 */
import pivotIcon from '@/assets/pivot-icon.png';

export default function PivotLogo({ height = 28 }: { height?: number }) {
  return (
    <span className="pivot-logo" style={{ height }}>
      <img src={pivotIcon} alt="" aria-hidden="true" height={height} style={{ width: 'auto' }} />
      <span className="pivot-logo__word">PIVOT</span>
    </span>
  );
}
