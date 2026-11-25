import { X } from 'lucide-react';

import { categoryLabel, typeLabel } from '../../lib/knowledge';
import type { EntryListParams } from '../../types/knowledge';

interface ActiveFiltersProps {
  params: EntryListParams;
  onClearQuery: () => void;
  onCategory: (value: string | null) => void;
  onSubcategory: (value: string | null) => void;
  onType: () => void;
  onTag: (tag: string) => void;
  onClearAll: () => void;
}

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-0.5 text-xs text-secondary-foreground">
      {label}
      <button type="button" aria-label={`移除 ${label}`} onClick={onRemove} className="rounded-full hover:bg-black/10">
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}

export function ActiveFilters({
  params,
  onClearQuery,
  onCategory,
  onSubcategory,
  onType,
  onTag,
  onClearAll,
}: ActiveFiltersProps) {
  const chips: { key: string; label: string; remove: () => void }[] = [];
  if (params.q) chips.push({ key: 'q', label: `关键词：${params.q}`, remove: onClearQuery });
  if (params.category !== null) {
    chips.push({ key: 'category', label: `分类：${categoryLabel(params.category)}`, remove: () => onCategory(null) });
  }
  if (params.subcategory !== null) {
    chips.push({
      key: 'subcategory',
      label: `子类：${categoryLabel(params.subcategory)}`,
      remove: () => onSubcategory(null),
    });
  }
  if (params.type) {
    chips.push({ key: 'type', label: `类型：${typeLabel(params.type)}`, remove: onType });
  }
  for (const tag of params.tags) {
    chips.push({ key: `tag-${tag}`, label: `标签：${tag}`, remove: () => onTag(tag) });
  }

  if (chips.length === 0) return null;

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {chips.map((chip) => (
        <Chip key={chip.key} label={chip.label} onRemove={chip.remove} />
      ))}
      <button type="button" onClick={onClearAll} className="text-xs text-muted-foreground underline hover:text-foreground">
        清空全部
      </button>
    </div>
  );
}
