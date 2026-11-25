import { useEffect, useMemo, useState } from 'react';

export type AsyncState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: T };

interface Entry<T> {
  request: object;
  state: AsyncState<T>;
}

/**
 * Loads data with cancellation. `load` must be memoized by the caller (useCallback). The result is tied to the
 * identity of (load, reloadKey): a new request is reported as loading without calling setState inside the effect.
 * To retry or refresh, the caller increments reloadKey.
 */
export function useAsyncResource<T>(load: (signal: AbortSignal) => Promise<T>, reloadKey = 0): AsyncState<T> {
  const [entry, setEntry] = useState<Entry<T> | null>(null);
  const request = useMemo(() => ({ load, reloadKey }), [load, reloadKey]);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setEntry({ request, state: { status: 'ready', data } });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message = error instanceof Error ? error.message : '加载失败';
        setEntry({ request, state: { status: 'error', message } });
      });
    return () => controller.abort();
  }, [load, request]);

  return entry && entry.request === request ? entry.state : { status: 'loading' };
}
