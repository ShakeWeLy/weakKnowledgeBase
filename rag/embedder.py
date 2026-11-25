"""Sentence-transformers wrapper that loads a local model directory."""

from __future__ import annotations

from typing import Sequence

from rag.config import EMBED_BATCH_SIZE, EMBED_DEVICE, EMBED_MODEL_PATH


class BlogEmbedder:
    def __init__(self, model_path: str = EMBED_MODEL_PATH, device: str = EMBED_DEVICE) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_path = model_path
        self.model = SentenceTransformer(model_path, device=device)
        self.dim = int(self.model.get_sentence_embedding_dimension())
        # E5 models expect "query: " / "passage: " prefixes; other models take raw text.
        self.is_e5 = "e5" in model_path.lower()

    def _prefixed(self, texts: Sequence[str], kind: str) -> list[str]:
        if not self.is_e5:
            return list(texts)
        return [f"{kind}: {t}" for t in texts]

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self.model.encode(
            self._prefixed(texts, "passage"),
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(
            self._prefixed([text], "query")[0],
            normalize_embeddings=True,
        )
        return vector.tolist()
