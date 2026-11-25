"""Shared fixtures: a temporary blogs/ directory with known content and an isolated SQLite database per test."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config import Settings
from main import create_app

PNG_BYTES = b"\x89PNG\r\n\x1a\n-test-image-"

BLOG_FILES: dict[str, str] = {
    "a.md": """---
title: 深度学习基础
date: 2026-01-02 10:00:00
category: AI & ML
subcategory: DL
tags:
  - dl
  - python
---
# 1 简介

卷积神经网络 CNN 是一种常见模型。

![pic](./a/pic.png)

语义分割 是对像素分类。
""",
    "b.md": """---
title: Unet 详解
date: 2026-02-01
category: AI & ML
subcategory: CV
tags:
  - model
  - segmentation
  - dl
---
Unet 是一个 U 形网络，常用于语义分割。
""",
    "无头文件.md": "没有 frontmatter 的文件，Milvus 向量库用于存储 embedding。\n",
    "容器部署.md": """---
title: 容器部署
category: Engineering
subcategory: Toolchain
type: paper
tags: docker, linux
---
docker 容器化部署流程。
""",
    "e.md": """---
type: weird
---
没有分类的条目。
""",
}


@pytest.fixture
def blogs_dir(tmp_path: Path) -> Path:
    root = tmp_path / "blogs"
    root.mkdir()
    for name, content in BLOG_FILES.items():
        (root / name).write_text(content, encoding="utf-8")
    (root / ".hidden.md").write_text("---\ntitle: hidden\n---\n隐藏文件", encoding="utf-8")
    (root / "a").mkdir()
    (root / "a" / "pic.png").write_bytes(PNG_BYTES)
    # A file next to blogs/ that must never be reachable through the asset endpoint.
    (tmp_path / "secret.png").write_bytes(b"secret")
    return root


@pytest.fixture
def settings(tmp_path: Path, blogs_dir: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.sqlite3').as_posix()}",
        blogs_dir=blogs_dir,
        sync_on_startup=False,
        cors_origins=("http://localhost:5173",),
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def synced_client(client: TestClient) -> TestClient:
    response = client.post("/api/knowledge/sync")
    assert response.status_code == 200, response.text
    return client


def find_by_title(items: list[dict], title: str) -> dict:
    matches = [item for item in items if item["title"] == title]
    assert len(matches) == 1, f"expected one entry titled {title!r}, got {len(matches)}"
    return matches[0]


def list_titles(client: TestClient, **params) -> list[str]:
    response = client.get("/api/knowledge/entries", params=params)
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]
