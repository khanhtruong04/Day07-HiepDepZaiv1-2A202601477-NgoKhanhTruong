from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Tách câu dựa trên các dấu kết thúc câu: ". ", "! ", "? ", ".\n"
        # Dùng regex để tách nhưng giữ lại dấu phân cách
        parts = re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text)

        # Lọc bỏ các phần rỗng
        sentences = [s.strip() for s in parts if s.strip()]

        if not sentences:
            return [text.strip()] if text.strip() else []

        # Nhóm các câu lại thành chunks
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_text = " ".join(group).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Bắt đầu đệ quy với toàn bộ danh sách separators
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Nếu văn bản đủ nhỏ, trả về ngay
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text.strip() else []

        # Nếu không còn separator nào, cắt thô theo chunk_size
        if not remaining_separators:
            # Cắt theo ký tự, không có separator
            chunks: list[str] = []
            start = 0
            while start < len(current_text):
                chunks.append(current_text[start : start + self.chunk_size])
                start += self.chunk_size
            return chunks

        # Lấy separator ưu tiên cao nhất hiện tại
        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Nếu separator rỗng (""), cắt theo từng ký tự
        if separator == "":
            chunks = []
            start = 0
            while start < len(current_text):
                chunks.append(current_text[start : start + self.chunk_size])
                start += self.chunk_size
            return chunks

        # Tách văn bản theo separator hiện tại
        parts = current_text.split(separator)

        # Gộp lại các phần có cùng separator
        result: list[str] = []
        current_chunk = ""

        for i, part in enumerate(parts):
            # Tái tạo phần văn bản với separator (trừ phần cuối)
            segment = part + (separator if i < len(parts) - 1 else "")

            if len(current_chunk) + len(segment) <= self.chunk_size:
                current_chunk += segment
            else:
                # Lưu chunk hiện tại nếu có nội dung
                if current_chunk.strip():
                    # Kiểm tra nếu current_chunk vẫn còn quá lớn
                    if len(current_chunk) > self.chunk_size:
                        result.extend(self._split(current_chunk, next_separators))
                    else:
                        result.append(current_chunk)
                current_chunk = segment

        # Xử lý phần còn lại
        if current_chunk.strip():
            if len(current_chunk) > self.chunk_size:
                result.extend(self._split(current_chunk, next_separators))
            else:
                result.append(current_chunk)

        # Nếu không tách được gì (separator không tồn tại trong văn bản), thử separator tiếp theo
        if not result:
            return self._split(current_text, next_separators)

        return result


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # Tính độ lớn (norm) của mỗi vector
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))

    # Bảo vệ chia cho 0: nếu một trong hai vector có độ lớn bằng 0
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    # Cosine similarity = dot product / (norm_a * norm_b)
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # Khởi tạo cả ba chunker với cùng chunk_size
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=0)
        sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        # Chạy từng chiến lược
        fixed_chunks = fixed_chunker.chunk(text)
        sentence_chunks = sentence_chunker.chunk(text)
        recursive_chunks = recursive_chunker.chunk(text)

        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": round(avg_length, 2),
                "chunks": chunks,
            }

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
        }
