import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Sparkles } from 'lucide-react';

import { createRelation } from '../../api/knowledge';
import { ApiError } from '../../api/client';
import { typeLabel } from '../../lib/knowledge';
import type { EntryDetail } from '../../types/knowledge';

interface RecommendationListProps {
  entry: EntryDetail;
  onChanged: () => void;
}

/** Suggestions only: entries sharing tags. Nothing is linked until the user clicks. */
export function RecommendationList({ entry, onChanged }: RecommendationListProps) {
  const [linkingId, setLinkingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const link = async (targetId: string) => {
    setLinkingId(targetId);
    setError(null);
    try {
      await createRelation(entry.id, targetId);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '关联失败');
    } finally {
      setLinkingId(null);
    }
  };

  return (
    <section className="rounded-lg border bg-card p-4">
      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <Sparkles className="h-4 w-4" />
        相关推荐（共享标签）
      </h2>
      {error && <p role="alert" className="mb-2 text-xs text-destructive">{error}</p>}
      {entry.recommendations.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {entry.tags.length === 0 ? '该条目没有标签，无法推荐。' : '暂时没有共享标签的其他条目。'}
        </p>
      ) : (
        <ul className="space-y-2">
          {entry.recommendations.map((rec) => (
            <li key={rec.entry.id} className="flex items-start justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-accent/10">
              <div className="min-w-0">
                <Link to={`/knowledge/${rec.entry.id}`} className="block truncate text-sm hover:text-primary">
                  {rec.entry.title}
                </Link>
                <p className="text-xs text-muted-foreground">
                  {typeLabel(rec.entry.type)} · 共享 {rec.shared_tag_count} 个标签
                </p>
              </div>
              <button
                type="button"
                onClick={() => void link(rec.entry.id)}
                disabled={linkingId !== null}
                aria-label={`关联 ${rec.entry.title}`}
                className="shrink-0 rounded p-1 text-muted-foreground hover:text-foreground disabled:opacity-50"
              >
                <Plus className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
