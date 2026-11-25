import { Link } from 'react-router-dom';
import { Calendar, FolderTree } from 'lucide-react';

import type { EntrySummary } from '../../types/knowledge';
import { categoryLabel, formatDate, splitHighlight, typeLabel } from '../../lib/knowledge';

const MAX_VISIBLE_TAGS = 4

interface EntryCardProps {
  entry: EntrySummary;
  showSnippet: boolean;
}

function Highlighted({ text }: { text: string }) {
  return (
    <>
      {splitHighlight(text).map((part, index) =>
        part.hit ? (
          <mark key={index} className="rounded bg-primary/20 px-0.5 text-foreground">
            {part.text}
          </mark>
        ) : (
          <span key={index}>{part.text}</span>
        ),
      )}
    </>
  );
}

export function EntryCard({ entry, showSnippet }: EntryCardProps) {
  const body = showSnippet && entry.snippet ? entry.snippet : entry.summary;
  const visibleTags = entry.tags.slice(0, MAX_VISIBLE_TAGS);
  const hiddenTagCount = entry.tags.length - visibleTags.length;

  return (
    <article className="flex flex-col gap-3 rounded-lg border bg-card p-4 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <Link to={`/knowledge/${entry.id}`} className="line-clamp-2 text-base font-semibold text-foreground hover:text-primary">
          {entry.title}
        </Link>
        <span className="shrink-0 rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
          {typeLabel(entry.type)}
        </span>
      </div>

      <p className="line-clamp-3 min-h-[3.75rem] text-sm text-muted-foreground">
        {body ? (showSnippet && entry.snippet ? <Highlighted text={body} /> : body) : '（无摘要）'}
      </p>

      <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <FolderTree className="h-3.5 w-3.5" />
          {categoryLabel(entry.category)}
          {entry.subcategory && <span> / {categoryLabel(entry.subcategory)}</span>}
        </span>
        <span className="inline-flex items-center gap-1">
          <Calendar className="h-3.5 w-3.5" />
          {formatDate(entry.source_created_at)}
        </span>
      </div>

      {entry.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {visibleTags.map((tag) => (
            <span key={tag} className="rounded-full border border-input px-2 py-0.5 text-xs text-muted-foreground">
              {tag}
            </span>
          ))}
          {hiddenTagCount > 0 && <span className="text-xs text-muted-foreground">+{hiddenTagCount}</span>}
        </div>
      )}
    </article>
  );
}
