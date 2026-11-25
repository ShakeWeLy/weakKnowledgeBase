import { useEffect, useState } from 'react';
import { Search, X } from 'lucide-react';

import { cn } from '../../lib/utils';

const DEBOUNCE_MS = 300;

interface SearchInputProps {
  value: string;
  onCommit: (value: string) => void;
  placeholder: string;
  className?: string;
}

/** Debounced search box. The URL is only updated after typing pauses, so each keystroke does not fire a request. */
export function SearchInput({ value, onCommit, placeholder, className }: SearchInputProps) {
  const [draft, setDraft] = useState(value);
  const [synced, setSynced] = useState(value);

  // Adopt external changes (back/forward, cleared filters) without an effect that sets state.
  if (value !== synced) {
    setSynced(value);
    setDraft(value);
  }

  useEffect(() => {
    if (draft.trim() === value) return;
    const timer = window.setTimeout(() => onCommit(draft), DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [draft, value, onCommit]);

  return (
    <div className={cn('relative', className)}>
      <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
      <input
        type="search"
        aria-label="搜索知识条目"
        value={draft}
        placeholder={placeholder}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') onCommit(draft);
        }}
        className="h-9 w-full rounded-md border border-input bg-transparent px-9 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      />
      {draft && (
        <button
          type="button"
          aria-label="清空搜索"
          onClick={() => {
            setDraft('');
            onCommit('');
          }}
          className="absolute right-2 top-2 rounded p-0.5 text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
