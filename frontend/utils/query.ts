export function buildQueryString(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === "") {
      return;
    }
    query.set(key, String(value));
  });

  const encoded = query.toString();
  return encoded ? `?${encoded}` : "";
}

export function toDateTimeStart(date: string | undefined): string | undefined {
  return date ? `${date}T00:00:00Z` : undefined;
}

export function toDateTimeEnd(date: string | undefined): string | undefined {
  return date ? `${date}T23:59:59Z` : undefined;
}
