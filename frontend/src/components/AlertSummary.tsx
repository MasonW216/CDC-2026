/**
 * Grouped, expandable rendering of a route's official alerts -- replaces the flat
 * `AlertList` `<ul>` for a route-level alert array, which could be 20+ identical lines
 * ("Flash Flood Warning" repeated once per county) with no county attached. Groups by
 * `event`, shows a count, and expands to the distinct counties for that event (joined
 * client-side from `route.segments[].alerts`, no backend change needed).
 *
 * Still renders above any advisory/recommendation wherever it is placed -- that ordering
 * rule lives in the caller's layout, not here.
 */
import { useState } from 'react';

import type { RouteScore } from '@/types/score';

interface AlertGroup {
  event: string;
  floor: number;
  counties: string[];
}

function groupAlerts(route: RouteScore): AlertGroup[] {
  const byEvent = new Map<string, AlertGroup>();
  for (const segment of route.segments) {
    for (const alert of segment.alerts) {
      const group = byEvent.get(alert.event) ?? { event: alert.event, floor: alert.floor, counties: [] };
      if (!group.counties.includes(segment.county_name)) group.counties.push(segment.county_name);
      byEvent.set(alert.event, group);
    }
  }
  return [...byEvent.values()].sort((a, b) => b.floor - a.floor);
}

function GroupChip({ group }: { group: AlertGroup }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li>
      <button type="button" className="alert-summary__group" aria-expanded={expanded} onClick={() => setExpanded((v) => !v)}>
        {group.event} &times;{group.counties.length}
      </button>
      {expanded && (
        <p className="note">{group.counties.join(', ')}</p>
      )}
    </li>
  );
}

export default function AlertSummary({ route }: { route: RouteScore }) {
  const groups = groupAlerts(route);
  if (groups.length === 0) return null;
  return (
    <div role="alert" className="alert-banner alert-summary">
      <h4>Official NWS flood products</h4>
      <ul>
        {groups.map((group) => (
          <GroupChip key={group.event} group={group} />
        ))}
      </ul>
    </div>
  );
}
