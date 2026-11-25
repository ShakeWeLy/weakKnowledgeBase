import { KnowledgeBrowser } from '../components/knowledge/KnowledgeBrowser';

/** 知识探索：分类/类型/标签筛选 + 关键词过滤 + 排序分页。 */
export function KnowledgeExplorerPage() {
  return <KnowledgeBrowser mode="explore" />;
}
