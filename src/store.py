from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # Khởi tạo ChromaDB client và collection
            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Xây dựng một bản ghi lưu trữ chuẩn hóa cho một tài liệu."""
        embedding = self._embedding_fn(doc.content)
        record = {
            "id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": dict(doc.metadata),  # copy để tránh tham chiếu ngoài
        }
        # Gắn doc_id vào metadata để phục vụ tìm kiếm và xóa
        record["metadata"]["doc_id"] = doc.id
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Tìm kiếm tương đồng trong bộ nhớ trên danh sách records được cung cấp."""
        if not records:
            return []

        query_embedding = self._embedding_fn(query)

        # Tính điểm dot product cho từng record
        scored = []
        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored.append({
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score,
            })

        # Sắp xếp theo điểm giảm dần và lấy top_k
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma and self._collection is not None:
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            for doc in docs:
                embedding = self._embedding_fn(doc.content)
                meta = dict(doc.metadata)
                meta["doc_id"] = doc.id
                ids.append(f"{doc.id}_{self._next_index}")
                self._next_index += 1
                documents.append(doc.content)
                embeddings.append(embedding)
                metadatas.append(meta)
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            # In-memory fallback
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            n_results = min(top_k, self._collection.count())
            if n_results == 0:
                return []
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            output = []
            for i, doc_id in enumerate(results["ids"][0]):
                output.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1.0 - results["distances"][0][i],  # chuyển distance thành score
                })
            return output
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            # Không có filter, tìm trên toàn bộ store
            return self.search(query, top_k=top_k)

        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            # Chuyển metadata_filter sang dạng ChromaDB where clause
            where = {k: {"$eq": v} for k, v in metadata_filter.items()} if len(metadata_filter) > 1 else metadata_filter
            n_results = min(top_k, self._collection.count())
            if n_results == 0:
                return []
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=metadata_filter,
            )
            output = []
            for i, doc_id in enumerate(results["ids"][0]):
                output.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1.0 - results["distances"][0][i],
                })
            return output
        else:
            # In-memory: lọc theo metadata trước, sau đó tìm kiếm
            filtered = []
            for record in self._store:
                meta = record.get("metadata", {})
                # Kiểm tra tất cả các điều kiện lọc
                match = all(meta.get(k) == v for k, v in metadata_filter.items())
                if match:
                    filtered.append(record)
            return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            # Lấy tất cả ids của doc_id trong collection
            results = self._collection.get(where={"doc_id": doc_id})
            ids_to_delete = results.get("ids", [])
            if ids_to_delete:
                self._collection.delete(ids=ids_to_delete)
                return True
            return False
        else:
            # In-memory: xóa tất cả records có metadata['doc_id'] == doc_id
            original_size = len(self._store)
            self._store = [
                record for record in self._store
                if record.get("metadata", {}).get("doc_id") != doc_id
            ]
            return len(self._store) < original_size
