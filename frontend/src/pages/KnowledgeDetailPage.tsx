import { useCallback, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

import { fetchEntry } from '../api/knowledge';
import { useAsyncResource } from '../hooks/useAsyncResource';
import { EntryMeta } from '../components/knowledge/EntryMeta';
import { MarkdownBody } from '../components/knowledge/MarkdownBody';
import { RecommendationList } from '../components/knowledge/RecommendationList';
import { RelationPanel } from '../components/knowledge/RelationPanel';
import { ErrorBlock, LoadingBlock } from '../components/common/StateBlock';

function BackLink() {
  return (
    <Link to="/knowledge" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
      <ArrowLeft className="h-4 w-4" />
      返回知识探索
    </Link>
  );
}

/** 知识详情：正文、元信息、手动关联与标签推荐。 */
export function KnowledgeDetailPage() {
  const { entryId = '' } = useParams();
  const [reloadKey, setReloadKey] = useState(0);
  const load = useCallback((signal: AbortSignal) => fetchEntry(entryId, signal), [entryId]);
  const state = useAsyncResource(load, reloadKey);
  const refresh = () => setReloadKey((k) => k + 1);

  if (state.status === 'loading') {
    return (
      <div className="w-full space-y-6 p-6">
        <BackLink />
        <LoadingBlock label="加载条目…" />
      </div>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="w-full space-y-6 p-6">
        <BackLink />
        <ErrorBlock message={state.message} onRetry={refresh} />
      </div>
    );
  }

  const entry = state.data;
  return (
    <div className="w-full p-6">
      <BackLink />
      <div className="mt-4 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <article className="min-w-0">
          <h1 className="text-2xl font-bold text-foreground">{entry.title}</h1>
          <div className="mt-3">
            <EntryMeta
              entry={entry}
              showDates={{ created: entry.source_created_at, updated: entry.source_updated_at }}
            />
          </div>
          {entry.summary && (
            <p className="mt-4 rounded-md bg-secondary/60 p-3 text-sm text-secondary-foreground">{entry.summary}</p>
          )}
          <div className="mt-6 rounded-lg border bg-card p-6">
            <MarkdownBody content={entry.content} />
          </div>
          <p className="mt-3 text-xs text-muted-foreground">来源文件：{entry.source_path}</p>
        </article>

        <aside className="space-y-6">
          <RelationPanel entry={entry} onChanged={refresh} />
          <RecommendationList entry={entry} onChanged={refresh} />
        </aside>
      </div>
    </div>
  );
}
