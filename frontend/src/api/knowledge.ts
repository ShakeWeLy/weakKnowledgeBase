import { apiRequest } from './client';
import type { EntryDetail, EntryListParams, EntryPage, Facets, RelationOut, SyncResult } from '../types/knowledge';

const BASE = '/api/knowledge';

/** Query string for /entries (with paging) or /facets (without paging, so facets do not refetch per page). */
export function buildListQuery(params: EntryListParams, withPaging: boolean): string {
  const query = new URLSearchParams();
  if (params.q) query.set('q', params.q);
  if (params.category) query.set('category', params.category);
  if (params.subcategory) query.set('subcategory', params.subcategory);
  if (params.type) query.set('type', params.type);
  for (const tag of params.tags) query.append('tag', tag);
  if (params.sort) query.set('sort', params.sort);
  if (params.order === 'asc') query.set('order', 'asc');
  if (withPaging) {
    query.set('page', String(params.page));
    query.set('page_size', String(params.pageSize));
  }
  const text = query.toString();
  return text ? `?${text}` : '';
}

export function fetchEntryPage(query: string, signal?: AbortSignal): Promise<EntryPage> {
  return apiRequest<EntryPage>(`${BASE}/entries${query}`, { signal });
}

export function fetchFacets(query: string, signal?: AbortSignal): Promise<Facets> {
  return apiRequest<Facets>(`${BASE}/facets${query}`, { signal });
}

export function fetchEntry(entryId: string, signal?: AbortSignal): Promise<EntryDetail> {
  return apiRequest<EntryDetail>(`${BASE}/entries/${encodeURIComponent(entryId)}`, { signal });
}

export function createRelation(entryId: string, targetId: string): Promise<RelationOut> {
  return apiRequest<RelationOut>(`${BASE}/entries/${encodeURIComponent(entryId)}/relations`, {
    method: 'POST',
    json: { target_id: targetId },
  });
}

export function removeRelation(relationId: string): Promise<void> {
  return apiRequest<void>(`${BASE}/relations/${encodeURIComponent(relationId)}`, { method: 'DELETE' });
}

export function syncKnowledge(): Promise<SyncResult> {
  return apiRequest<SyncResult>(`${BASE}/sync`, { method: 'POST' });
}

/** URL for an image referenced by a blog (path relative to blogs/). Backend only serves image files. */
export function assetUrl(relativePath: string): string {
  const clean = relativePath.replace(/^\.\//, '').replace(/^\/+/, '');
  return `${BASE}/assets/${clean.split('/').map(encodeURIComponent).join('/')}`;
}
