import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Link2, Plus, Trash2 } from 'lucide-react';

import { removeRelation } from '../../api/knowledge';
import { ApiError } from '../../api/client';
import { typeLabel } from '../../lib/knowledge';
import type { EntryDetail } from '../../types/knowledge';
import { RelationPicker } from './RelationPicker';

interface RelationPanelProps {
  entry: EntryDetail;
  onChanged: () => void;
}

/** Manual relations (both directions are shown). Adding and removing both refresh the detail page. */
export function RelationPanel({ entry, onChanged }: RelationPanelProps) {
  const [picking, setPicking] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const remove = async (relationId: string) => {
    if (!window.confirm('确定取消这条关联吗？')) return;
    setRemovingId(relationId);
    setError(null);
    try {
      await removeRelation(relationId);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '取消关联失败');
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <section className="rounded-lg border bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Link2 className="h-4 w-4" />
          关联知识（{entry.relations.length}）
        </h2>
        <button
          type="button"
          onClick={() => setPicking(true)}
          className="inline-flex items-center gap-1 rounded-md border border-input px-2 py-1 text-xs hover:bg-accent hover:text-accent-foreground"
        >
          <Plus className="h-3 w-3" />
          添加
        </button>
      </div>

      {error && <p role="alert" className="mb-2 text-xs text-destructive">{error}</p>}

      {entry.relations.length === 0 ? (
        <p className="text-sm text-muted-foreground">还没有手动关联。可以在下方推荐中挑选，或点击“添加”。</p>
      ) : (
        <ul className="space-y-2">
          {entry.relations.map((relation) => (
            <li key={relation.relation_id} className="flex items-start justify-between gap-2 rounded-md border px-3 py-2">
              <div className="min-w-0">
                <Link to={`/knowledge/${relation.entry.id}`} className="block truncate text-sm font-medium hover:text-primary">
                  {relation.entry.title}
                </Link>
                <p className="text-xs text-muted-foreground">{typeLabel(relation.entry.type)}</p>
              </div>
              <button
                type="button"
                onClick={() => void remove(relation.relation_id)}
                disabled={removingId !== null}
                aria-label={`取消关联 ${relation.entry.title}`}
                className="shrink-0 rounded p-1 text-muted-foreground hover:text-destructive disabled:opacity-50"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {picking && (
        <RelationPicker
          entry={entry}
          onClose={() => setPicking(false)}
          onLinked={() => {
            onChanged();
          }}
        />
      )}
    </section>
  );
}
