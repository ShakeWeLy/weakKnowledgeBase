"""End-to-end tests for the knowledge API against a real SQLite file and real markdown fixtures."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from sqlalchemy import event
from fastapi.testclient import TestClient

from internal.db import get_engine
from services.blog_parser import parse_blog
from tests.conftest import PNG_BYTES, find_by_title, list_titles


# ---------------------------------------------------------------- sync

def test_sync_imports_all_top_level_markdown(client: TestClient) -> None:
    response = client.post("/api/knowledge/sync")
    assert response.status_code == 200
    assert response.json() == {"added": 5, "updated": 0, "unchanged": 0, "removed": 0}

    listing = client.get("/api/knowledge/entries", params={"page_size": 50}).json()
    assert listing["total"] == 5  # .hidden.md is ignored
    titles = {item["title"] for item in listing["items"]}
    assert titles == {"深度学习基础", "Unet 详解", "无头文件", "容器部署", "e"}


def test_sync_is_incremental_and_handles_edit_delete_restore(synced_client: TestClient, blogs_dir: Path) -> None:
    client = synced_client
    assert client.post("/api/knowledge/sync").json() == {"added": 0, "updated": 0, "unchanged": 5, "removed": 0}

    original_id = find_by_title(client.get("/api/knowledge/entries", params={"page_size": 50}).json()["items"], "无头文件")["id"]

    (blogs_dir / "b.md").write_text("Unet 改写后的正文，只讲 Attention。\n", encoding="utf-8")
    assert client.post("/api/knowledge/sync").json() == {"added": 0, "updated": 1, "unchanged": 4, "removed": 0}

    (blogs_dir / "无头文件.md").unlink()
    assert client.post("/api/knowledge/sync").json() == {"added": 0, "updated": 0, "unchanged": 4, "removed": 1}
    assert client.get("/api/knowledge/entries", params={"page_size": 50}).json()["total"] == 4
    assert client.get(f"/api/knowledge/entries/{original_id}").status_code == 404

    (blogs_dir / "无头文件.md").write_text("重新出现的文件，Milvus 向量库。\n", encoding="utf-8")
    assert client.post("/api/knowledge/sync").json() == {"added": 0, "updated": 1, "unchanged": 4, "removed": 0}
    restored = client.get(f"/api/knowledge/entries/{original_id}")
    assert restored.status_code == 200  # same row id: restored, not re-created


def test_sync_refuses_missing_blogs_dir_and_keeps_data(synced_client: TestClient, settings) -> None:
    synced_client.app.state.settings = replace(settings, blogs_dir=settings.blogs_dir.parent / "missing")
    response = synced_client.post("/api/knowledge/sync")
    assert response.status_code == 503
    assert synced_client.get("/api/knowledge/entries").json()["total"] == 5


# ---------------------------------------------------------------- list / filter / sort / paginate

def test_filters_by_category_subcategory_type_and_tags(synced_client: TestClient) -> None:
    client = synced_client
    assert len(list_titles(client, category="AI & ML", page_size=50)) == 2
    assert list_titles(client, subcategory="DL") == ["深度学习基础"]
    assert list_titles(client, type="paper") == ["容器部署"]
    assert sorted(list_titles(client, tag="dl")) == ["Unet 详解", "深度学习基础"]
    assert list_titles(client, tag=["dl", "python"]) == ["深度学习基础"]  # tags combine with AND
    assert sorted(list_titles(client, category="__none__", page_size=50)) == ["e", "无头文件"]


def test_sorting_by_title_and_date(synced_client: TestClient) -> None:
    client = synced_client
    assert list_titles(client, sort="title", order="asc", page_size=50) == [
        "Unet 详解",
        "e",
        "容器部署",
        "无头文件",
        "深度学习基础",
    ]
    newest_first = list_titles(client, sort="source_created_at", order="desc", page_size=50)
    assert newest_first[:2] == ["Unet 详解", "深度学习基础"]  # entries without a date sort last


def test_pagination_reports_total_and_pages(synced_client: TestClient) -> None:
    client = synced_client
    page2 = client.get("/api/knowledge/entries", params={"page_size": 2, "page": 2, "sort": "title", "order": "asc"})
    body = page2.json()
    assert body["total"] == 5 and body["page"] == 2 and body["page_size"] == 2
    assert [item["title"] for item in body["items"]] == ["容器部署", "无头文件"]
    last = client.get("/api/knowledge/entries", params={"page_size": 2, "page": 3}).json()
    assert len(last["items"]) == 1


def test_invalid_query_parameters_are_rejected(synced_client: TestClient) -> None:
    client = synced_client
    assert client.get("/api/knowledge/entries", params={"page_size": 0}).status_code == 422
    assert client.get("/api/knowledge/entries", params={"page_size": 101}).status_code == 422
    assert client.get("/api/knowledge/entries", params={"type": "bogus"}).status_code == 422
    assert client.get("/api/knowledge/entries", params={"sort": "drop table"}).status_code == 422


def test_list_query_count_does_not_grow_with_rows(synced_client: TestClient) -> None:
    """Tags are eager-loaded, so the number of SQL statements must not depend on the number of rows."""
    statements: list[str] = []
    engine = get_engine()

    def record(_conn, _cursor, statement, *_args) -> None:  # type: ignore[no-untyped-def]
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        synced_client.get("/api/knowledge/entries", params={"page_size": 1})
        one_row = len(statements)
        statements.clear()
        synced_client.get("/api/knowledge/entries", params={"page_size": 5})
        five_rows = len(statements)
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert five_rows == one_row


# ---------------------------------------------------------------- keyword search (FTS5 trigram)

def test_chinese_fts_search_with_highlighted_snippet(synced_client: TestClient) -> None:
    response = synced_client.get("/api/knowledge/entries", params={"q": "语义分割"})
    body = response.json()
    assert body["total"] == 2
    assert all(item["snippet"] and "[[语义分割]]" in item["snippet"] for item in body["items"])


def test_fts_is_case_insensitive_and_excludes_archived(synced_client: TestClient, blogs_dir: Path) -> None:
    assert list_titles(synced_client, q="UNET") == ["Unet 详解"]
    assert list_titles(synced_client, q="milvus") == ["无头文件"]
    (blogs_dir / "无头文件.md").unlink()
    synced_client.post("/api/knowledge/sync")
    assert list_titles(synced_client, q="milvus") == []


def test_short_query_falls_back_to_like(synced_client: TestClient) -> None:
    assert list_titles(synced_client, q="向量") == ["无头文件"]  # 2 characters: below trigram minimum


def test_query_operators_are_treated_as_plain_text(synced_client: TestClient) -> None:
    assert synced_client.get("/api/knowledge/entries", params={"q": 'a OR "b" *'}).status_code == 200
    assert synced_client.get("/api/knowledge/entries", params={"q": '"'}).status_code == 200


def test_relevance_sort_is_default_for_keyword_search(synced_client: TestClient) -> None:
    titles = list_titles(synced_client, q="语义分割")
    assert set(titles) == {"深度学习基础", "Unet 详解"}


# ---------------------------------------------------------------- detail

def test_detail_contains_content_tags_and_type(synced_client: TestClient) -> None:
    items = synced_client.get("/api/knowledge/entries", params={"page_size": 50}).json()["items"]
    entry = find_by_title(items, "深度学习基础")
    detail = synced_client.get(f"/api/knowledge/entries/{entry['id']}").json()
    assert detail["type"] == "technical_note"
    assert detail["tags"] == ["dl", "python"]
    assert "语义分割" in detail["content"]
    assert detail["relations"] == []


def test_detail_404_for_unknown_id(synced_client: TestClient) -> None:
    assert synced_client.get("/api/knowledge/entries/does-not-exist").status_code == 404


# ---------------------------------------------------------------- relations

def _ids_by_title(client: TestClient) -> dict[str, str]:
    items = client.get("/api/knowledge/entries", params={"page_size": 50}).json()["items"]
    return {item["title"]: item["id"] for item in items}


def test_relation_create_conflict_self_and_missing(synced_client: TestClient) -> None:
    client = synced_client
    ids = _ids_by_title(client)
    a, b = ids["深度学习基础"], ids["Unet 详解"]

    created = client.post(f"/api/knowledge/entries/{a}/relations", json={"target_id": b})
    assert created.status_code == 201
    relation_id = created.json()["relation_id"]

    assert client.post(f"/api/knowledge/entries/{b}/relations", json={"target_id": a}).status_code == 409
    assert client.post(f"/api/knowledge/entries/{a}/relations", json={"target_id": a}).status_code == 400
    assert client.post(f"/api/knowledge/entries/{a}/relations", json={"target_id": "nope"}).status_code == 404
    assert client.post("/api/knowledge/entries/nope/relations", json={"target_id": b}).status_code == 404

    from_a = client.get(f"/api/knowledge/entries/{a}").json()["relations"]
    from_b = client.get(f"/api/knowledge/entries/{b}").json()["relations"]
    assert [r["entry"]["title"] for r in from_a] == ["Unet 详解"]
    assert [r["entry"]["title"] for r in from_b] == ["深度学习基础"]

    assert client.delete(f"/api/knowledge/relations/{relation_id}").status_code == 204
    assert client.get(f"/api/knowledge/entries/{a}").json()["relations"] == []
    assert client.delete(f"/api/knowledge/relations/{relation_id}").status_code == 404


def test_relations_to_archived_entries_are_hidden_but_kept(synced_client: TestClient, blogs_dir: Path) -> None:
    client = synced_client
    ids = _ids_by_title(client)
    a, b = ids["深度学习基础"], ids["Unet 详解"]
    client.post(f"/api/knowledge/entries/{a}/relations", json={"target_id": b})

    (blogs_dir / "b.md").unlink()
    client.post("/api/knowledge/sync")
    assert client.get(f"/api/knowledge/entries/{a}").json()["relations"] == []


# ---------------------------------------------------------------- recommendations and facets

def test_recommendations_share_tags_and_exclude_related(synced_client: TestClient) -> None:
    client = synced_client
    ids = _ids_by_title(client)
    a, b = ids["深度学习基础"], ids["Unet 详解"]

    recs = client.get(f"/api/knowledge/entries/{a}").json()["recommendations"]
    assert [(r["entry"]["title"], r["shared_tag_count"]) for r in recs] == [("Unet 详解", 1)]

    client.post(f"/api/knowledge/entries/{a}/relations", json={"target_id": b})
    assert client.get(f"/api/knowledge/entries/{a}").json()["recommendations"] == []


def test_facets_follow_current_filters(synced_client: TestClient) -> None:
    client = synced_client
    facets = client.get("/api/knowledge/facets").json()
    categories = {item["value"]: item["count"] for item in facets["categories"]}
    assert categories == {"AI & ML": 2, "Engineering": 1, None: 2}
    assert {item["value"]: item["count"] for item in facets["types"]} == {"technical_note": 4, "paper": 1}
    tags = {item["value"]: item["count"] for item in facets["tags"]}
    assert tags["dl"] == 2 and tags["docker"] == 1

    filtered = client.get("/api/knowledge/facets", params={"q": "语义分割"}).json()
    assert {item["value"]: item["count"] for item in filtered["categories"]} == {"AI & ML": 2}


# ---------------------------------------------------------------- assets

def test_asset_served_only_from_blogs_dir_with_image_suffix(synced_client: TestClient) -> None:
    client = synced_client
    ok = client.get("/api/knowledge/assets/a/pic.png")
    assert ok.status_code == 200 and ok.content == PNG_BYTES

    assert client.get("/api/knowledge/assets/..%2Fsecret.png").status_code == 404  # traversal
    assert client.get("/api/knowledge/assets/a.md").status_code == 404  # not an image
    assert client.get("/api/knowledge/assets/missing.png").status_code == 404


# ---------------------------------------------------------------- parser

def test_parser_reads_frontmatter_and_skips_code_for_summary() -> None:
    raw = (
        "---\n"
        "title: T\n"
        "date: 2026-03-04\n"
        "type: concept\n"
        "tags: [a, b, ' a ', '']\n"
        "---\n"
        "```py\n# not a heading\n```\n"
        "# H\n\n"
        "first paragraph text\n"
    )
    parsed = parse_blog("fallback", raw)
    assert parsed.title == "T"
    assert parsed.entry_type == "concept"
    assert parsed.tags == ["a", "b"]
    assert parsed.source_created_at is not None and parsed.source_created_at.year == 2026
    assert parsed.summary == "first paragraph text"


def test_summary_is_plain_text_even_inside_quotes() -> None:
    raw = "> ### 状态空间表示\n> 正文第一句 **加粗** 与 `code`\n"
    assert parse_blog("fallback", raw).summary == "正文第一句 加粗 与 code"
    assert parse_blog("fallback", "> ### 只有标题\n").summary == ""


def test_search_text_strips_markdown_syntax_but_keeps_words() -> None:
    raw = "## 2 为什么 **语义分割** 的主要矛盾\n\n见 [论文](http://x) 与 `Conv2d`。![img](./a.png)\n"
    parsed = parse_blog("fallback", raw)
    assert "**" not in parsed.search_text and "`" not in parsed.search_text and "#" not in parsed.search_text
    assert "语义分割 的主要矛盾" in parsed.search_text
    assert "见 论文 与 Conv2d。" in parsed.search_text
    assert "![" not in parsed.search_text and "./a.png" not in parsed.search_text
