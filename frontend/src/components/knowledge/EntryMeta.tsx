import { Calendar, FolderTree, Tag } from 'lucide-react';

import { categoryLabel, formatDate, typeLabel } from '../../lib/knowledge';
import type { EntryBrief } from '../../types/knowledge';

/** Category / subcategory / type / tags line used by the detail header and relation list. */
export function EntryMeta({ entry, showDates }: { entry: EntryBrief; showDates?: { created: string | null; updated: string | null } }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
      <span className="inline-flex items-center gap-1">
        <FolderTree className="h-4 w-4" />
        {categoryLabel(entry.category)}
        {entry.subcategory && <span> / {categoryLabel(entry.subcategory)}</span>}
      </span>
      <span className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">{typeLabel(entry.type)}</span>
      {entry.tags.length > 0 && (
        <span className="inline-flex flex-wrap items-center gap-1.5">
          <Tag className="h-4 w-4" />
          {entry.tags.map((tag) => (
            <span key={tag} className="rounded-full border border-input px-2 py-0.5 text-xs">
              {tag}
            </span>
          ))}
        </span>
      )}
      {showDates && (
        <span className="inline-flex items-center gap-1">
          <Calendar className="h-4 w-4" />
          创建 {formatDate(showDates.created)} · 更新 {formatDate(showDates.updated)}
        </span>
      )}
    </div>
  );
}
