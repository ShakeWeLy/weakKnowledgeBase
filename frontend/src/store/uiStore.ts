import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;
export type PageSize = (typeof PAGE_SIZE_OPTIONS)[number];

/**
 * UI preferences only. Filter/sort/page state lives in the URL so it survives refresh and can be shared;
 * keeping it out of the store avoids two sources of truth.
 */
interface UiState {
  pageSize: PageSize;
  setPageSize: (size: PageSize) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      pageSize: 20,
      setPageSize: (pageSize) => set({ pageSize }),
    }),
    { name: 'weakkb-ui' },
  ),
);
