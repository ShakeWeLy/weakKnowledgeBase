---
name: blogs category细分
overview: 为 blogs 下有 frontmatter 的 Markdown 批量写入 category/subcategory（保留 tags）；Deploy/CUDA 等归入 AI & ML / Deploy；并同步扩展手稿中的二级分类表。
todos:
  - id: script-classify
    content: 实现 frontmatter 写入 category/subcategory 的分类脚本（含优先级与硬覆盖）
    status: completed
  - id: batch-apply
    content: 对 blogs 有 frontmatter 的 md 批量应用并校验统计
    status: completed
  - id: update-manuscript
    content: 更新手稿.md Category 二级分类表（Deploy/ML/DL/Toolchain）
    status: completed
isProject: false
---

# blogs Category / Subcategory 细分方案

## 目标

给每篇有 YAML frontmatter 的 [`blogs/*.md`](blogs) 增加：

```yaml
category: AI & ML
subcategory: Deploy
```

- **保留**现有 `tags`
- 字段插在 `date` 与 `tags` 之间
- 4 篇无 frontmatter 跳过：`.Todo.md`、`git.md`、`效果对比.md`、`算法设计.md`

## 分类取值（一级固定 6 个）

与手稿一致：`AI & ML` · `Medical AI` · `Engineering` · `Research` · `Project` · `Personal`

二级在手稿基础上扩展（本批会写入 [`手稿.md`](手稿.md) 分类表）：

| 一级 | 二级（本批使用） |
|------|------------------|
| AI & ML | CV、NLP、LLM、Agent、**Deploy**、**ML**、**DL** |
| Medical AI | MRI（本批暂无单独 Segmentation/Neuroimaging 条目；通用分割模型归 CV） |
| Engineering | Python、PyTorch、Backend、**Toolchain** |
| Research | 本批暂无命中（MRI 论文复现按领域归 Medical AI） |
| Project | Agent、Detection |
| Personal | Learning、Reflection、Career |

## 判定优先级（脚本规则）

按文件名 + tags，**先匹配先生效**：

1. 文件名/`mri` → `Medical AI` / `MRI`
2. 面试/`interview`、第一份工作总结 → `Personal` / `Career`
3. 天池/`tianchi`、自制框架 → `Project` / `Detection`；`rag_project` → `Project` / `Agent`
4. tags ∈ {agent,rag,vlm,vla} → `AI & ML` / `Agent`
5. `llm` → `AI & ML` / `LLM`（特例：`VAEmodel` → `DL`）
6. `nlp` → `AI & ML` / `NLP`
7. tags ∈ {deploy,onnx,tensorrt,quant,cuda} → `AI & ML` / `Deploy`
8. tags ∈ {cv,tracking,yolo,segmentation} 或 DETR/YOLO/MOT 等文件名 → `AI & ML` / `CV`
9. `ml` → `AI & ML` / `ML`；其余 `model`/`dl` → `CV` 或 `DL`
10. Engineering：web/前后端/vue/fastapi/SSE/cpp → `Backend`；纯 torch 工程向可标 `PyTorch`；python/chore 及 Linux/docker/git/uv/anfi/cmake → `Python` 或 `Toolchain`
11. 其余 misc → `Personal` / `Learning` 或 `Reflection`

**硬覆盖**：`C-计划` → Personal/Reflection；`工程设计` → Engineering/Backend。

## 预估规模（约 197 篇）

- AI & ML：Agent ~34 · Deploy ~31 · CV ~29 · DL ~26 · ML ~9 · LLM ~5–6 · NLP ~2
- Engineering：Python/Toolchain/Backend ~25+
- Medical AI / MRI：10
- Project：~9
- Personal：~15+

## 执行步骤

1. 写一次性脚本：解析 frontmatter → 按上表分类 → 写入 `category`/`subcategory`（幂等：已有则覆盖为规范值）
2. 跑脚本并校验：无空 category；统计各 (category, subcategory) 数量；抽查 Deploy/MRI/面试样例
3. 更新 [`手稿.md`](手稿.md) §1 Category 表格，补上 Deploy、ML、DL、Toolchain

## 不做

- 不改 tags、不改文件名、不挪目录
- 不为本批补 Research / Medical Segmentation 空二级（无对应内容则不硬塞）
