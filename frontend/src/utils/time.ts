const dateFormatter = new Intl.DateTimeFormat(undefined, {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

const timeFormatter = new Intl.DateTimeFormat(undefined, {
  hour: "numeric",
  minute: "2-digit",
});

const weekdayFormatter = new Intl.DateTimeFormat(undefined, {
  weekday: "long",
  hour: "numeric",
  minute: "2-digit",
});

function parseUtcTimestamp(value: string): Date {
  return new Date(value.endsWith("Z") || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`);
}

function isSameLocalDate(left: Date, right: Date) {
  return left.getFullYear() === right.getFullYear() && left.getMonth() === right.getMonth() && left.getDate() === right.getDate();
}

export function formatLocalDateTime(value: string): string {
  const date = parseUtcTimestamp(value);
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (isSameLocalDate(date, now)) return `Today, ${timeFormatter.format(date)}`;
  if (isSameLocalDate(date, yesterday)) return `Yesterday, ${timeFormatter.format(date)}`;
  return dateFormatter.format(date);
}

export function formatTimelineTime(value: string): string {
  const date = parseUtcTimestamp(value);
  const now = new Date();
  if (isSameLocalDate(date, now)) return timeFormatter.format(date);
  return weekdayFormatter.format(date);
}

export function formatRelativeTime(value: string): string {
  const diffSeconds = Math.round((Date.now() - parseUtcTimestamp(value).getTime()) / 1000);
  const suffix = diffSeconds >= 0 ? "ago" : "from now";
  const abs = Math.abs(diffSeconds);
  if (abs < 60) return `${abs} second${abs === 1 ? "" : "s"} ${suffix}`;
  const minutes = Math.round(abs / 60);
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ${suffix}`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ${suffix}`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ${suffix}`;
}
