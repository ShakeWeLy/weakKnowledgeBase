import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

import { parseListParams, buildSearchParams } from '../lib/urlParams';
import type { EntryListParams, EntryType, SortKey, SortOrder } from '../types/knowledge';

type Patch = Partial<EntryListParams>;

/**
 * Filter state backed by the URL. Every change returns to page 1 unless it is a page change.
 * Replace (not push) keeps browser history from filling up while typing or clicking filters.
 */
export function useEntryFilters(pageSize: number) {
  const [search, setSearch] = useSearchParams();
  const params = useMemo(() => parseListParams(search, pageSize), [search, pageSize]);

  const update = useCallback(
    (compute: (current: EntryListParams) => Patch, resetPage: boolean) => {
      setSearch(
        (prev) => {
          const current = parseListParams(prev, pageSize);
          const next: EntryListParams = { ...current, ...compute(current) };
          if (resetPage) next.page = 1;
          return buildSearchParams(next);
        },
        { replace: true },
      );
    },
    [setSearch, pageSize],
  );

  const setQuery = useCallback((q: string) => update(() => ({ q: q.trim() }), true), [update]);

  const setCategory = useCallback(
    (category: string | null) => update(() => ({ category, subcategory: null }), true),
    [update],
  );

  const setSubcategory = useCallback((subcategory: string | null) => update(() => ({ subcategory }), true), [update]);

  const setType = useCallback((type: EntryType | null) => update(() => ({ type }), true), [update]);

  const toggleTag = useCallback(
    (tag: string) =>
      update(
        (current) => ({
          tags: current.tags.includes(tag) ? current.tags.filter((t) => t !== tag) : [...current.tags, tag],
        }),
        true,
      ),
    [update],
  );

  const setSort = useCallback(
    (sort: SortKey | null, order: SortOrder) => update(() => ({ sort, order }), true),
    [update],
  );

  const setPage = useCallback((page: number) => update(() => ({ page }), false), [update]);

  const clearFilters = useCallback(
    () => update(() => ({ q: '', category: null, subcategory: null, type: null, tags: [] }), true),
    [update],
  );

  return { params, setQuery, setCategory, setSubcategory, setType, toggleTag, setSort, setPage, clearFilters };
}
