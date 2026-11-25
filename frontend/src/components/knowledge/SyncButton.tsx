import { useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';

import { syncKnowledge } from '../../api/knowledge';
import type { SyncResult } from '../../types/knowledge';

interface SyncButtonProps {
  onDone: () => void;
}

function describe(result: SyncResult): string {
  const parts = [`新增 ${result.added}`, `更新 ${result.updated}`, `删除 ${result.removed}`, `未变 ${result.unchanged}`];
  return `同步完成：${parts.join('，')}`;
}

/** Re-reads blogs/*.md. Only changed files are re-indexed, so pressing it repeatedly is cheap. */
export function SyncButton({ onDone }: SyncButtonProps) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null);

  const handleClick = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const result = await syncKnowledge();
      setMessage({ kind: 'ok', text: describe(result) });
      onDone();
    } catch (error) {
      setMessage({ kind: 'error', text: error instanceof Error ? error.message : '同步失败' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex items-center gap-3">
      {message && (
        <span role="status" className={message.kind === 'ok' ? 'text-xs text-muted-foreground' : 'text-xs text-destructive'}>
          {message.text}
        </span>
      )}
      <button
        type="button"
        onClick={() => void handleClick()}
        disabled={busy}
        className="inline-flex h-9 items-center gap-2 rounded-md border border-input px-3 text-sm hover:bg-accent hover:text-accent-foreground disabled:opacity-60"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
        同步 blogs
      </button>
    </div>
  );
}
