import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { Layout } from './components/Layout';
import { LoadingBlock } from './components/common/StateBlock';
import { KnowledgeExplorerPage } from './pages/KnowledgeExplorerPage';
import { KnowledgeSearchPage } from './pages/KnowledgeSearchPage';
import { NotFoundPage } from './pages/NotFoundPage';

// The detail page pulls in the markdown renderer and highlight.js, so it is loaded on demand.
const KnowledgeDetailPage = lazy(() =>
  import('./pages/KnowledgeDetailPage').then((module) => ({ default: module.KnowledgeDetailPage })),
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/knowledge" replace />} />
          <Route path="knowledge" element={<KnowledgeExplorerPage />} />
          <Route path="knowledge/search" element={<KnowledgeSearchPage />} />
          <Route
            path="knowledge/:entryId"
            element={
              <Suspense fallback={<LoadingBlock label="加载页面…" />}>
                <KnowledgeDetailPage />
              </Suspense>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
