/**
 * Interpret a planner date/time input as North Carolina wall-clock time and
 * render it as ISO 8601 with an explicit UTC offset (build guide section 13's
 * "Score request" example: `"2024-09-27T12:00:00-04:00"`).
 *
 * North Carolina is entirely in the America/New_York zone, so this needs no
 * per-county lookup -- only the Eastern/Daylight offset for the chosen date.
 * `Intl.DateTimeFormat` is used instead of a date library so the frontend adds
 * no new dependency for one conversion.
 */

const ZONE = 'America/New_York';

/**
 * UTC offset, in minutes, for America/New_York at `instant`.
 *
 * Positive would mean ahead of UTC; Eastern is always behind, so this is
 * negative (-300 in EST, -240 in EDT).
 */
function offsetMinutesAt(instant: Date): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: ZONE,
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).formatToParts(instant);
  const get = (type: string) => Number(parts.find((part) => part.type === type)?.value ?? 0);
  const asUtc = Date.UTC(
    get('year'),
    get('month') - 1,
    get('day'),
    get('hour') % 24, // Intl can format midnight as "24"
    get('minute'),
    get('second'),
  );
  return Math.round((asUtc - instant.getTime()) / 60_000);
}

function formatOffset(minutes: number): string {
  const sign = minutes <= 0 ? '-' : '+';
  const abs = Math.abs(minutes);
  const hh = String(Math.floor(abs / 60)).padStart(2, '0');
  const mm = String(abs % 60).padStart(2, '0');
  return `${sign}${hh}:${mm}`;
}

/**
 * Convert an `<input type="datetime-local">` value (`"2024-09-27T12:00"`, no
 * timezone) into an ISO 8601 string with the correct America/New_York offset
 * for that date.
 *
 * The offset for a wall-clock time is computed from that same time treated as
 * a UTC instant -- exact away from a DST transition, and off by at most an
 * hour for the one wall-clock hour each spring/fall that is skipped or
 * repeated. That known limit is acceptable here: the planner is not used to
 * schedule trips inside a DST transition hour.
 *
 * @throws {Error} if `localValue` is not a valid datetime-local value.
 */
export function toEasternIso(localValue: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(localValue);
  if (!match) {
    throw new Error(`not a datetime-local value: ${localValue}`);
  }
  const [, year, month, day, hour, minute, second = '00'] = match;
  const pseudoUtc = new Date(
    Date.UTC(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hour),
      Number(minute),
      Number(second),
    ),
  );
  if (Number.isNaN(pseudoUtc.getTime())) {
    throw new Error(`not a valid date/time: ${localValue}`);
  }
  const offset = offsetMinutesAt(pseudoUtc);
  const stamp = `${year}-${month}-${day}T${hour}:${minute}:${second}`;
  return `${stamp}${formatOffset(offset)}`;
}
