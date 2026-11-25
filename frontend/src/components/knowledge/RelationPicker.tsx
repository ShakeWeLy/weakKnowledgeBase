import { useEffect, useMemo, useState } from 'react';
import { Link2, Loader2, X } from 'lucide-react';

import { buildListQuery, createRelation, fetchEntryPage } from '../../api/knowledge';
import { ApiError } from '../../api/client';
import { useAsyncResource } from '../../hooks/useAsyncResource';
import { typeLabel } from '../../lib/knowledge';
import type { EntryListParams, EntryDetail } from '../../types/knowledge';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '../common/StateBlock';

const PICKER_PAGE_SIZE = 10;
const DEBOUNCE_MS = 250;

interface RelationPickerProps {
  entry: EntryDetail;
  onClose: () => void;
  onLinked: () => void;
}

/** Search the library and link the current entry to a chosen one. Self and existing relations are hidden. */
export function RelationPicker({ entry, onClose, onLinked }: RelationPickerProps) {
  const [input, setInput] = useState('');
  const [keyword, setKeyword] = useState('');
  const [linkingId, setLinkingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setKeyword(input.trim()), DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [input]);

  const query = useMemo(() => {
    const params: EntryListParams = {
      q: keyword,
      category: null,
      subcategory: null,
      type: null,
      tags: [],
      sort: null,
      order: 'desc',
      page: 1,
      pageSize: PICKER_PAGE_SIZE,
    };
    return buildListQuery(params, true);
  }, [keyword]);
  const load = useMemo(() => (signal: AbortSignal) => fetchEntryPage(query, signal), [query]);
  const result = useAsyncResource(load);

  const linked = useMemo(() => new Set(entry.relations.map((r) => r.entry.id)), [entry.relations]);

  const link = async (targetId: string) => {
    setLinkingId(targetId);
    setError(null);
    try {
      await createRelation(entry.id, targetId);
      onLinked();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '关联失败，请稍后重试');
    } finally {
      setLinkingId(null);
    }
  };

  const candidates = result.status === 'ready' ? result.data.items.filter((item) => item.id !== entry.id && !linked.has(item.id)) : [];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 p-6 pt-24" role="dialog" aria-modal="true" aria-label="添加关联">
      <div className="w-full max-w-lg rounded-lg border bg-card shadow-lg">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-sm font-semibold">添加关联</h2>
          <button type="button" onClick={onClose} aria-label="关闭" className="rounded p-1 text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-3 p-4">
          <input
            autoFocus
            type="search"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="输入标题或关键词搜索要关联的条目"
            className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

          {result.status === 'loading' && <LoadingBlock label="搜索中…" />}
          {result.status === 'error' && <ErrorBlock message={result.message} />}
          {result.status === 'ready' && candidates.length === 0 && (
            <EmptyBlock title={keyword ? '没有可关联的条目' : '输入关键词查找条目'} />
          )}

          {result.status === 'ready' && candidates.length > 0 && (
            <ul className="max-h-80 space-y-1 overflow-y-auto">
              {candidates.map((item) => (
                <li key={item.id} className="flex items-center justify-between gap-3 rounded-md px-2 py-2 hover:bg-accent/10">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{item.title}</p>
                    <p className="text-xs text-muted-foreground">{typeLabel(item.type)}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void link(item.id)}
                    disabled={linkingId !== null}
                    className="inline-flex shrink-0 items-center gap-1 rounded-md border border-input px-2 py-1 text-xs hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
                  >
                    {linkingId === item.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Link2 className="h-3 w-3" />}
                    关联
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
