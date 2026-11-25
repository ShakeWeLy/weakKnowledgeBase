import { useState, type ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

import { cn } from '../../lib/utils';
import { categoryLabel, NO_CATEGORY, typeLabel } from '../../lib/knowledge';
import type { EntryListParams, EntryType, Facets, FacetValue } from '../../types/knowledge';
import { AsyncHint } from './AsyncHint';

const TAG_PREVIEW_COUNT = 30;

interface FilterPanelProps {
  params: EntryListParams;
  facets: Facets | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onCategory: (value: string | null) => void;
  onSubcategory: (value: string | null) => void;
  onType: (value: EntryType | null) => void;
  onTag: (tag: string) => void;
}

function FacetButton({
  active,
  label,
  count,
  onClick,
  nested = false,
}: {
  active: boolean;
  label: string;
  count: number;
  onClick: () => void;
  nested?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm transition-colors hover:bg-accent/10',
        nested && 'pl-6 text-muted-foreground',
        active && 'bg-secondary font-medium text-secondary-foreground',
      )}
    >
      <span className="truncate">{label}</span>
      <span className="ml-2 shrink-0 text-xs text-muted-foreground">{count}</span>
    </button>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</h2>
      {children}
    </section>
  );
}

export function FilterPanel({
  params,
  facets,
  loading,
  error,
  onRetry,
  onCategory,
  onSubcategory,
  onType,
  onTag,
}: FilterPanelProps) {
  const [showAllTags, setShowAllTags] = useState(false);

  if (loading && !facets) return <AsyncHint text="加载筛选项…" />;
  if (error && !facets) {
    return (
      <AsyncHint
        text={error}
        action={
          <button type="button" onClick={onRetry} className="text-primary underline">
            重试
          </button>
        }
      />
    );
  }
  if (!facets) return null;

  const activeCategory = params.category;
  const subcategories = facets.subcategories.filter((s) => s.category === (activeCategory === NO_CATEGORY ? null : activeCategory));
  const tags: FacetValue[] = showAllTags ? facets.tags : facets.tags.slice(0, TAG_PREVIEW_COUNT);

  return (
    <div>
      <Section title="分类">
        {facets.categories.map((item) => {
          const value = item.value ?? NO_CATEGORY;
          const active = activeCategory === value;
          return (
            <div key={value}>
              <FacetButton
                active={active}
                label={categoryLabel(item.value)}
                count={item.count}
                onClick={() => onCategory(active ? null : value)}
              />
              {active &&
                subcategories.map((sub) => {
                  const subValue = sub.value ?? NO_CATEGORY;
                  return (
                    <FacetButton
                      key={subValue}
                      nested
                      active={params.subcategory === subValue}
                      label={categoryLabel(sub.value)}
                      count={sub.count}
                      onClick={() => onSubcategory(params.subcategory === subValue ? null : subValue)}
                    />
                  );
                })}
            </div>
          );
        })}
        {facets.categories.length === 0 && <p className="px-2 text-sm text-muted-foreground">暂无分类</p>}
      </Section>

      <Section title="类型">
        {facets.types.map((item) => {
          const type = item.value as EntryType;
          return (
            <FacetButton
              key={type}
              active={params.type === type}
              label={typeLabel(type)}
              count={item.count}
              onClick={() => onType(params.type === type ? null : type)}
            />
          );
        })}
        {facets.types.length === 0 && <p className="px-2 text-sm text-muted-foreground">暂无类型</p>}
      </Section>

      <Section title="标签">
        <div className="flex flex-wrap gap-1.5">
          {tags.map((item) => {
            const name = item.value ?? '';
            const active = params.tags.includes(name);
            return (
              <button
                key={name}
                type="button"
                aria-pressed={active}
                onClick={() => onTag(name)}
                className={cn(
                  'rounded-full border px-2.5 py-0.5 text-xs transition-colors',
                  active
                    ? 'border-primary bg-primary text-primary-foreground'
                    : 'border-input text-muted-foreground hover:text-foreground',
                )}
              >
                {name} <span className="opacity-70">{item.count}</span>
              </button>
            );
          })}
        </div>
        {facets.tags.length > TAG_PREVIEW_COUNT && (
          <button
            type="button"
            onClick={() => setShowAllTags((v) => !v)}
            className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            {showAllTags ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            {showAllTags ? '收起' : `显示全部 ${facets.tags.length} 个`}
          </button>
        )}
        {facets.tags.length === 0 && <p className="text-sm text-muted-foreground">暂无标签</p>}
      </Section>
    </div>
  );
}
