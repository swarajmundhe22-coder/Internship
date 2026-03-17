export type QueryState = Record<string, string>;

export type UpdateQueryOptions = {
  resetPage?: boolean;
  pageKey?: string;
};

export function mergeQueryState(defaults: QueryState, incoming: Record<string, string | string[] | undefined>): QueryState {
  const merged = { ...defaults };

  Object.entries(incoming).forEach(([key, value]) => {
    const normalized = Array.isArray(value) ? value[0] : value;
    if (typeof normalized === "string") {
      merged[key] = normalized;
    }
  });

  return merged;
}

export function buildNextQueryState(
  current: QueryState,
  patch: Record<string, string | undefined>,
  options?: UpdateQueryOptions
): QueryState {
  const next = { ...current };

  Object.entries(patch).forEach(([key, value]) => {
    if (value === undefined || value === "") {
      delete next[key];
    } else {
      next[key] = value;
    }
  });

  if (options?.resetPage ?? true) {
    next[options?.pageKey ?? "page"] = "1";
  }

  return next;
}

export function hasQueryStateChanged(current: QueryState, next: QueryState): boolean {
  const keys = new Set([...Object.keys(current), ...Object.keys(next)]);
  return Array.from(keys).some((key) => (current[key] ?? "") !== (next[key] ?? ""));
}
