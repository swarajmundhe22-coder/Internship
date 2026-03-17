import { useRouter } from "next/router";
import { useMemo } from "react";

type UpdateOptions = {
  resetPage?: boolean;
};

import {
  buildNextQueryState,
  hasQueryStateChanged,
  mergeQueryState,
  QueryState
} from "../utils/QueryStateManager";

export function useUrlQueryState(defaults: QueryState) {
  const router = useRouter();

  const state = useMemo<QueryState>(() => {
    return mergeQueryState(defaults, router.query);
  }, [router.query, defaults]);

  function setQuery(patch: Record<string, string | undefined>, options?: UpdateOptions) {
    const next = buildNextQueryState(state, patch, {
      resetPage: options?.resetPage,
      pageKey: "page"
    });

    if (!hasQueryStateChanged(state, next)) {
      return;
    }

    void router.push(
      {
        pathname: router.pathname,
        query: next
      },
      undefined,
      { shallow: true }
    );
  }

  return { state, setQuery, isReady: router.isReady };
}
