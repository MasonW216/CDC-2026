/**
 * One bar per route, length = its 0-100 index, colored by band -- replaces the bare-prose
 * "Comparison" card with something faster to read than two sentences. The only use of
 * `recharts` in this codebase (installed, unused until now); used exactly once, on
 * purpose, not as decoration.
 *
 * Only rendered when there is a real, distinguishable comparison to show: a tie or an
 * `unavailable`/`single_route`/`no_routes` ranking never gets a bar chart, so this can
 * never visually imply a "safer route" the backend itself declined to claim (the same
 * rule `LiveRoutePage`'s `routeColor()` already enforces for map coloring).
 */
import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from 'recharts';

import type { Comparison, RouteScore } from '@/types/score';
import { BAND_CLASS } from '@/utils/scoreDisplay';

// Reads the same CSS custom properties LevelBadge/RouteMap use, at render time, so the
// chart always matches the badge colors and inherits dark mode for free.
function resolveColor(band: string): string {
  const cssVar = {
    'level-badge--0': '--level-0-fg',
    'level-badge--1': '--level-1-fg',
    'level-badge--2': '--level-2-fg',
    'level-badge--3': '--level-3-fg',
    'level-badge--none': '--level-none-fg',
  }[BAND_CLASS[band] ?? 'level-badge--none']!;
  return getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim() || '#888';
}

interface RouteComparisonChartProps {
  routes: RouteScore[];
  comparison: Comparison;
  labels: Record<string, string>;
}

export default function RouteComparisonChart({
  routes,
  comparison,
  labels,
}: RouteComparisonChartProps) {
  const chartable = comparison.ranking === 'distinguishable' || comparison.ranking === 'tie';
  const scored = routes.filter((r) => r.index !== null);
  if (!chartable || scored.length < 2) return null;

  const data = scored.map((route) => ({
    name: labels[route.route_id] ?? route.route_id,
    index: route.index ?? 0,
    band: route.band,
    fill: resolveColor(route.band),
  }));

  return (
    <div className="comparison-chart" role="img" aria-label={comparison.message}>
      <ResponsiveContainer width="100%" height={Math.max(80, data.length * 56)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 64, left: 8, bottom: 4 }}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            type="category"
            dataKey="name"
            width={90}
            tick={{ fontSize: 13 }}
            axisLine={false}
            tickLine={false}
          />
          <Bar dataKey="index" radius={4} barSize={24} isAnimationActive={false}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
            <LabelList
              dataKey="index"
              position="right"
              formatter={(value: number) => `${Math.round(value)}/100`}
              style={{ fontSize: 12, fontWeight: 600 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
