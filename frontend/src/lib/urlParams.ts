import { ENTRY_TYPES } from './knowledge';
import type { EntryListParams, EntryType, SortKey, SortOrder } from '../types/knowledge';

const SORT_KEYS: SortKey[] = ['relevance', 'source_created_at', 'source_updated_at', 'title'];

/** Reads filter/sort/page state from the URL. Unknown or invalid values fall back to defaults. */
export function parseListParams(search: URLSearchParams, pageSize: number): EntryListParams {
  const sort = search.get('sort') as SortKey | null;
  const type = search.get('type') as EntryType | null;
  const order: SortOrder = search.get('order') === 'asc' ? 'asc' : 'desc';
  const page = Math.max(1, Number.parseInt(search.get('page') ?? '1', 10) || 1);
  return {
    q: (search.get('q') ?? '').trim(),
    category: search.get('category') || null,
    subcategory: search.get('subcategory') || null,
    type: type && ENTRY_TYPES.includes(type) ? type : null,
    tags: search.getAll('tag').filter(Boolean),
    sort: sort && SORT_KEYS.includes(sort) ? sort : null,
    order,
    page,
    pageSize,
  };
}

/** Writes only non-default values so shared links stay short. */
export function buildSearchParams(params: EntryListParams): URLSearchParams {
  const search = new URLSearchParams();
  if (params.q) search.set('q', params.q);
  if (params.category) search.set('category', params.category);
  if (params.subcategory) search.set('subcategory', params.subcategory);
  if (params.type) search.set('type', params.type);
  for (const tag of params.tags) search.append('tag', tag);
  if (params.sort) search.set('sort', params.sort);
  if (params.order === 'asc') search.set('order', 'asc');
  if (params.page > 1) search.set('page', String(params.page));
  return search;
}
