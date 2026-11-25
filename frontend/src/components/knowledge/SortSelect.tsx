import type { SortKey, SortOrder } from '../../types/knowledge';
import { SORT_OPTIONS, sortOptionId, type SortOption } from '../../lib/knowledge';

interface SortSelectProps {
  mode: 'explore' | 'search';
  sort: SortKey | null;
  order: SortOrder;
  onChange: (option: SortOption) => void;
}

export function SortSelect({ mode, sort, order, onChange }: SortSelectProps) {
  const options = SORT_OPTIONS.filter((option) => !option.searchOnly || mode === 'search');
  const current = sortOptionId(sort, order);
  return (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      排序
      <select
        value={current}
        onChange={(event) => {
          const option = options.find((o) => o.id === event.target.value);
          if (option) onChange(option);
        }}
        className="h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
