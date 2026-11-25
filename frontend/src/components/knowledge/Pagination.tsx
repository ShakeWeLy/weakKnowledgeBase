import { ChevronLeft, ChevronRight } from 'lucide-react';

import { PAGE_SIZE_OPTIONS, useUiStore, type PageSize } from '../../store/uiStore';

interface PaginationProps {
  page: number;
  total: number;
  pageSize: number;
  onPage: (page: number) => void;
}

export function Pagination({ page, total, pageSize, onPage }: PaginationProps) {
  const setPageSize = useUiStore((s) => s.setPageSize);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <nav aria-label="分页" className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
      <span className="text-muted-foreground">
        共 {total} 条 · 第 {Math.min(page, totalPages)} / {totalPages} 页
      </span>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-1 text-muted-foreground">
          每页
          <select
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value) as PageSize);
              onPage(1);
            }}
            className="h-8 rounded-md border border-input bg-background px-1"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => onPage(page - 1)}
          disabled={page <= 1}
          className="inline-flex h-8 items-center gap-1 rounded-md border border-input px-2 hover:bg-accent hover:text-accent-foreground disabled:opacity-40"
        >
          <ChevronLeft className="h-4 w-4" />
          上一页
        </button>
        <button
          type="button"
          onClick={() => onPage(page + 1)}
          disabled={page >= totalPages}
          className="inline-flex h-8 items-center gap-1 rounded-md border border-input px-2 hover:bg-accent hover:text-accent-foreground disabled:opacity-40"
        >
          下一页
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </nav>
  );
}
