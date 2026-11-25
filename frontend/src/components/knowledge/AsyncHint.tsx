import type { ReactNode } from 'react';

/** Small inline status text for side panels (loading, error) where a full state block would be too heavy. */
export function AsyncHint({ text, action }: { text: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col gap-2 px-2 py-3 text-sm text-muted-foreground">
      <span>{text}</span>
      {action}
    </div>
  );
}
