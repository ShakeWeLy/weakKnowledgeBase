import { KnowledgeBrowser } from '../components/knowledge/KnowledgeBrowser';

/** 全文检索：与知识探索共用筛选，结果展示命中片段并支持相关度排序。 */
export function KnowledgeSearchPage() {
  return <KnowledgeBrowser mode="search" />;
}
