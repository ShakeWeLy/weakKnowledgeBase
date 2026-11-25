import { useCallback, useMemo, useState } from 'react';

import { buildListQuery, fetchEntryPage, fetchFacets } from '../../api/knowledge';
import { useAsyncResource } from '../../hooks/useAsyncResource';
import { useEntryFilters } from '../../hooks/useEntryFilters';
import { hasActiveFilters, type SortOption } from '../../lib/knowledge';
import { useUiStore } from '../../store/uiStore';
import type { EntryPage, Facets } from '../../types/knowledge';
import { ActiveFilters } from './ActiveFilters';
import { EntryCard } from './EntryCard';
import { FilterPanel } from './FilterPanel';
import { Pagination } from './Pagination';
import { SearchInput } from './SearchInput';
import { SortSelect } from './SortSelect';
import { SyncButton } from './SyncButton';
import { EmptyBlock, ErrorBlock, SkeletonGrid } from '../common/StateBlock';

export type BrowserMode = 'explore' | 'search';

const TITLES: Record<BrowserMode, string> = {
  explore: '知识探索',
  search: '全文检索',
};

/** Shared layout for 知识探索 and 全文检索: filter sidebar + search/sort bar + card grid + pagination. */
export function KnowledgeBrowser({ mode }: { mode: BrowserMode }) {
  const pageSize = useUiStore((s) => s.pageSize);
  const filters = useEntryFilters(pageSize);
  const { params } = filters;
  const [reloadKey, setReloadKey] = useState(0);

  // Search mode shows nothing until the user types a query, so no list request is made without one.
  const skipList = mode === 'search' && !params.q;
  const listQuery = useMemo(() => buildListQuery(params, true), [params]);
  const facetQuery = useMemo(() => buildListQuery(params, false), [params]);

  const listLoad = useCallback(
    (signal: AbortSignal): Promise<EntryPage | null> =>
      skipList ? Promise.resolve(null) : fetchEntryPage(listQuery, signal),
    [skipList, listQuery],
  );
  const facetLoad = useCallback((signal: AbortSignal): Promise<Facets> => fetchFacets(facetQuery, signal), [facetQuery]);

  const list = useAsyncResource(listLoad, reloadKey);
  const facets = useAsyncResource(facetLoad, reloadKey);

  const retry = () => setReloadKey((k) => k + 1);
  const facetData = facets.status === 'ready' ? facets.data : null;
  const listData = list.status === 'ready' ? list.data : null;

  const applySort = (option: SortOption) => filters.setSort(option.sort, option.order);

  const renderResults = () => {
    if (skipList) {
      return (
        <EmptyBlock
          title="输入关键词开始检索"
          description="支持中文和英文，会搜索标题、摘要与正文。"
        />
      );
    }
    if (list.status === 'loading') return <SkeletonGrid />;
    if (list.status === 'error') return <ErrorBlock message={list.message} onRetry={retry} />;
    if (!listData) return null;

    if (listData.total === 0) {
      if (hasActiveFilters(params)) {
        return (
          <EmptyBlock
            title="没有符合条件的条目"
            description="试试放宽筛选条件，或清空关键词。"
            action={
              <button
                type="button"
                onClick={filters.clearFilters}
                className="rounded-md border border-input px-3 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground"
              >
                清空筛选
              </button>
            }
          />
        );
      }
      return (
        <EmptyBlock
          title="知识库还没有内容"
          description="请确认 BLOGS_DIR 指向正确的 md 目录，然后点击右上角“同步 blogs”。"
        />
      );
    }

    const totalPages = Math.max(1, Math.ceil(listData.total / listData.page_size));
    if (listData.items.length === 0 && params.page > totalPages) {
      return (
        <EmptyBlock
          title="这一页没有内容"
          action={
            <button
              type="button"
              onClick={() => filters.setPage(totalPages)}
              className="rounded-md border border-input px-3 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground"
            >
              回到最后一页
            </button>
          }
        />
      );
    }

    return (
      <>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {listData.items.map((entry) => (
            <EntryCard key={entry.id} entry={entry} showSnippet={mode === 'search'} />
          ))}
        </div>
        <Pagination page={params.page} total={listData.total} pageSize={pageSize} onPage={filters.setPage} />
      </>
    );
  };

  return (
    <div className="flex min-h-0 w-full flex-1">
      <aside className="w-64 shrink-0 overflow-y-auto border-r bg-card/40 p-4">
        <FilterPanel
          params={params}
          facets={facetData}
          loading={facets.status === 'loading'}
          error={facets.status === 'error' ? facets.message : null}
          onRetry={retry}
          onCategory={filters.setCategory}
          onSubcategory={filters.setSubcategory}
          onType={filters.setType}
          onTag={filters.toggleTag}
        />
      </aside>

      <section className="min-w-0 flex-1 p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-foreground">{TITLES[mode]}</h1>
            {listData && !skipList && (
              <p className="text-sm text-muted-foreground">
                {params.q ? `“${params.q}” 共 ${listData.total} 条结果` : `共 ${listData.total} 条知识`}
              </p>
            )}
          </div>
          <SyncButton onDone={retry} />
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-3">
          <SearchInput
            value={params.q}
            onCommit={filters.setQuery}
            placeholder={mode === 'search' ? '输入关键词，例如：语义分割、Milvus、量化' : '搜索标题、摘要或正文…'}
            className="min-w-64 flex-1"
          />
          <SortSelect
            mode={mode}
            // Keyword search without an explicit sort is ordered by relevance, so show that instead of "default".
            sort={params.sort ?? (mode === 'search' && params.q ? 'relevance' : null)}
            order={params.order}
            onChange={applySort}
          />
        </div>

        <ActiveFilters
          params={params}
          onClearQuery={() => filters.setQuery('')}
          onCategory={filters.setCategory}
          onSubcategory={filters.setSubcategory}
          onType={() => filters.setType(null)}
          onTag={filters.toggleTag}
          onClearAll={filters.clearFilters}
        />

        {renderResults()}
      </section>
    </div>
  );
}