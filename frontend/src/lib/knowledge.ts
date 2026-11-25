import type { EntryListParams, EntryType, SortKey, SortOrder } from '../types/knowledge';

/** Value used in filters and URLs for entries without a category (backend: category IS NULL). */
export const NO_CATEGORY = '__none__';

export const ENTRY_TYPE_LABELS: Record<EntryType, string> = {
  concept: '概念',
  technical_note: '技术笔记',
  paper: '论文',
  tutorial: '教程',
  experiment: '实验',
  project: '项目',
  post: '博客',
  reflection: '复盘',
  resource: '资源',
};

export const ENTRY_TYPES = Object.keys(ENTRY_TYPE_LABELS) as EntryType[];

export interface SortOption {
  id: string;
  label: string;
  sort: SortKey | null;
  order: SortOrder;
  /** Relevance only makes sense for keyword search. */
  searchOnly?: boolean;
}

export const SORT_OPTIONS: SortOption[] = [
  { id: 'default', label: '默认排序', sort: null, order: 'desc' },
  { id: 'created_desc', label: '创建时间 ↓', sort: 'source_created_at', order: 'desc' },
  { id: 'created_asc', label: '创建时间 ↑', sort: 'source_created_at', order: 'asc' },
  { id: 'updated_desc', label: '更新时间 ↓', sort: 'source_updated_at', order: 'desc' },
  { id: 'title_asc', label: '标题 A→Z', sort: 'title', order: 'asc' },
  { id: 'title_desc', label: '标题 Z→A', sort: 'title', order: 'desc' },
  { id: 'relevance', label: '相关度', sort: 'relevance', order: 'desc', searchOnly: true },
];

export function sortOptionId(sort: SortKey | null, order: SortOrder): string {
  const found = SORT_OPTIONS.find((option) => option.sort === sort && option.order === order);
  return found?.id ?? 'default';
}

export function hasActiveFilters(params: EntryListParams): boolean {
  return Boolean(
    params.q || params.category !== null || params.subcategory !== null || params.type !== null || params.tags.length > 0,
  );
}

export function categoryLabel(value: string | null): string {
  return value === null || value === NO_CATEGORY ? '未分类' : value;
}

export function typeLabel(type: EntryType): string {
  return ENTRY_TYPE_LABELS[type] ?? type;
}

export function formatDate(value: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
}

/** Splits "a[[b]]c" (backend snippet markup) into parts so React can render the highlight without innerHTML. */
export function splitHighlight(text: string): { text: string; hit: boolean }[] {
  const parts: { text: string; hit: boolean }[] = [];
  let last = 0;
  for (const match of text.matchAll(/\[\[(.*?)\]\]/g)) {
    const index = match.index ?? 0;
    if (index > last) parts.push({ text: text.slice(last, index), hit: false });
    parts.push({ text: match[1], hit: true });
    last = index + match[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last), hit: false });
  return parts;
}
