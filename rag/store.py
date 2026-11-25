"""Milvus storage for blog chunks."""

from __future__ import annotations

import json
from typing import Any, Optional

from pymilvus import DataType, MilvusClient

INSERT_BATCH = 500
OUTPUT_FIELDS = ["source", "title", "heading", "category", "subcategory", "tags", "text"]


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


class MilvusBlogStore:
    def __init__(self, uri: str, collection: str, dim: int) -> None:
        self.client = MilvusClient(uri=uri)
        self.collection = collection
        self.dim = dim

    def exists(self) -> bool:
        return self.client.has_collection(self.collection)

    def drop(self) -> None:
        if self.exists():
            self.client.drop_collection(self.collection)

    def ensure_collection(self) -> None:
        if self.exists():
            self.client.load_collection(self.collection)
            return
        schema = self.client.create_schema(auto_id=True, enable_dynamic_field=False)
        schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.dim)
        schema.add_field("source", DataType.VARCHAR, max_length=512)
        schema.add_field("title", DataType.VARCHAR, max_length=512)
        schema.add_field("heading", DataType.VARCHAR, max_length=1024)
        schema.add_field("category", DataType.VARCHAR, max_length=64)
        schema.add_field("subcategory", DataType.VARCHAR, max_length=64)
        schema.add_field("tags", DataType.VARCHAR, max_length=512)
        schema.add_field("text", DataType.VARCHAR, max_length=8192)

        index_params = self.client.prepare_index_params()
        index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE")
        self.client.create_collection(
            collection_name=self.collection,
            schema=schema,
            index_params=index_params,
        )
        self.client.load_collection(self.collection)

    def delete_source(self, source: str) -> None:
        self.client.delete(collection_name=self.collection, filter=f"source == {_quote(source)}")

    def insert(self, rows: list[dict[str, Any]]) -> None:
        for start in range(0, len(rows), INSERT_BATCH):
            self.client.insert(self.collection, rows[start : start + INSERT_BATCH])

    def flush(self) -> None:
        self.client.flush(self.collection)

    def search(
        self,
        vector: list[float],
        top_k: int,
        subcategory: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        expr = f"subcategory == {_quote(subcategory)}" if subcategory else None
        results = self.client.search(
            collection_name=self.collection,
            data=[vector],
            limit=top_k,
            filter=expr,
            output_fields=OUTPUT_FIELDS,
            search_params={"metric_type": "COSINE"},
        )
        hits = []
        for item in results[0]:
            entity = item.get("entity", {})
            hits.append({"score": float(item.get("distance", 0.0)), **entity})
        return hits
