// Mirrors backend/schemas/knowledge.py. Field names are the API's snake_case keys.

export type EntryType =
  | 'concept'
  | 'technical_note'
  | 'paper'
  | 'tutorial'
  | 'experiment'
  | 'project'
  | 'post'
  | 'reflection'
  | 'resource';

export type SortKey = 'relevance' | 'source_created_at' | 'source_updated_at' | 'title';
export type SortOrder = 'asc' | 'desc';

export interface EntryBrief {
  id: string;
  title: string;
  summary: string;
  category: string | null;
  subcategory: string | null;
  type: EntryType;
  tags: string[];
}

export interface EntrySummary extends EntryBrief {
  source_path: string;
  source_created_at: string | null;
  source_updated_at: string | null;
  snippet: string | null;
}

export interface EntryPage {
  items: EntrySummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface RelatedEntry {
  relation_id: string;
  entry: EntryBrief;
}

export interface Recommendation {
  entry: EntryBrief;
  shared_tag_count: number;
}

export interface EntryDetail extends EntryBrief {
  content: string;
  source_path: string;
  source_created_at: string | null;
  source_updated_at: string | null;
  relations: RelatedEntry[];
  recommendations: Recommendation[];
}

export interface FacetValue {
  value: string | null;
  count: number;
}

export interface SubcategoryFacet {
  category: string | null;
  value: string | null;
  count: number;
}

export interface Facets {
  categories: FacetValue[];
  subcategories: SubcategoryFacet[];
  types: FacetValue[];
  tags: FacetValue[];
}

export interface SyncResult {
  added: number;
  updated: number;
  unchanged: number;
  removed: number;
}

export interface RelationOut {
  relation_id: string;
  source_id: string;
  target_id: string;
  created_at: string;
}

/** Filter/sort/page state shared by the explorer and search pages (also the URL query). */
export interface EntryListParams {
  q: string;
  category: string | null;
  subcategory: string | null;
  type: EntryType | null;
  tags: string[];
  sort: SortKey | null;
  order: SortOrder;
  page: number;
  pageSize: number;
}
