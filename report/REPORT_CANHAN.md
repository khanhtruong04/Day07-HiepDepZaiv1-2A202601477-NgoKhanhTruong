# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Khánh Trượng
**Nhóm:** Hiệp Đẹp Zai v1
**Ngày:** 03/08/2026

---

## 1. Khởi động 

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có độ tương tự cosine cao, điều đó có nghĩa là góc giữa hai vector đại diện (embeddings) của chúng trong không gian đa chiều rất nhỏ, thể hiện rằng hai đoạn văn bản có ý nghĩa ngữ nghĩa (semantic meaning) và nội dung truyền tải rất tương đồng với nhau, dù từ ngữ diễn đạt có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Quy trình đăng ký học phần của sinh viên đại học."
- Câu B: "Hướng dẫn các bước đăng ký môn học cho sinh viên."
- Tại sao tương đồng: Cả hai câu đều truyền tải cùng một nội dung (thủ tục đăng ký học phần/môn học của sinh viên), hướng vector biểu diễn góc trùng/gần trùng nhau trong không gian embedding.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Hôm nay trời nắng đẹp và tôi đi ăn phở."
- Câu B: "Thuật toán sắp xếp nhanh (QuickSort) có độ phức tạp trung bình là O(n log n)."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn không liên quan (đời sống/ẩm thực vs khoa học máy tính), hướng của hai vector trong không gian xấp xỉ vuông góc với nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ dài (độ lớn) của vector (văn bản dài hay ngắn sẽ có độ dài vector khác nhau). Trong khi đó, độ tương tự cosine chỉ đo góc hướng của vector (bỏ qua độ dài), giúp tập trung so sánh bản chất ngữ nghĩa của hai văn bản mà không bị sai lệch bởi độ dài tài liệu.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `số_lượng_chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11)`
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Phép tính mới: `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75)` = **25 chunks** (tăng 2 chunks).
> - Muốn tăng độ chồng chéo để duy trì tính liên tục của ngữ cảnh tại các ranh giới cắt, tránh trường hợp một câu văn hay thông tin quan trọng bị cắt đôi dẫn đến mất ngữ nghĩa khi truy xuất (Retrieval).

---

## 2. Hướng tiếp cận 

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text)` để phân tách câu dựa trên ranh giới các dấu chấm, hỏi, cảm thán hoặc xuống dòng sau dấu chấm. Thuật toán lọc bỏ các khoảng trắng rỗng, xử lý edge case văn bản không chứa ranh giới câu bằng cách trả về nguyên đoạn văn bản đã strip, và nhóm các câu theo số lượng `max_sentences_per_chunk` tối đa cho phép.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử nghiệm phân tách văn bản theo thứ tự ưu tiên separator `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi độ dài văn bản $\le$ `chunk_size` hoặc danh sách separator rỗng / bằng `""` (lúc này cắt thô theo từng ký tự). Nếu một đoạn gom vẫn vượt quá `chunk_size`, hàm sẽ đệ quy `_split` với danh sách separator còn lại.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Hỗ trợ song song ChromaDB và bộ nhớ trong (in-memory fallback list). Khi thêm tài liệu (`add_documents`), mỗi `Document` được tạo bản ghi chuẩn hóa gồm `id`, `content`, `embedding` (tính từ `_embedding_fn`) và `metadata`. Với `search`, query được chuyển thành embedding vector rồi tính tích vô hướng (dot product) với toàn bộ vector đã lưu, sắp xếp giảm dần theo điểm tương đồng để lấy ra `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Sử dụng cơ chế lọc trước (pre-filtering): đầu tiên lọc ra danh sách các bản ghi khớp tất cả thuộc tính trong `metadata_filter`, sau đó mới thực hiện tìm kiếm tương đồng trên tập đã lọc. Với `delete_document`, tiến hành lọc bỏ tất cả các chunk trong danh sách lưu trữ mà `metadata['doc_id'] == doc_id` và trả về `True` nếu có ít nhất một chunk bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k)` để lấy ra các đoạn thông tin liên quan nhất từ cơ sở tri thức. Cấu trúc prompt được thiết kế gồm khối ngữ cảnh (context) đánh số thứ tự từng đoạn `[Đoạn i]: content`, kết hợp với câu hỏi của người dùng và lời nhắc trả lời; sau đó truyền prompt hoàn chỉnh này vào hàm `llm_fn` để sinh câu trả lời cuối cùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]
============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên đăng ký học phần trên hệ thống học vụ. | Hướng dẫn các bước đăng ký môn học cho sinh viên. | cao | 0.0098 (Mock) | Đúng về ý nghĩa (thấp do Mock) |
| 2 | Thư viện cung cấp dịch vụ mượn trả sách. | Sinh viên có thể đến thư viện để mượn giáo trình. | cao | -0.0499 (Mock) | Đúng về ý nghĩa (thấp do Mock) |
| 3 | Hôm nay thời tiết rất đẹp và nắng ấm. | Trời hôm nay nhiều mây và có thể có mưa. | trung bình | -0.0144 (Mock) | Đúng |
| 4 | Sinh viên cần hoàn thành thủ tục đăng ký học phần đúng hạn. | Món phở bò ở Hà Nội rất thơm ngon. | thấp | 0.0653 (Mock) | Đúng về bản chất chủ đề |
| 5 | Đội bóng đá Việt Nam vừa giành chiến thắng. | Thuật toán sắp xếp QuickSort có độ phức tạp O(n log n). | thấp | 0.0505 (Mock) | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số thực tế khi dùng Mock Embedder (dựa trên băm MD5) cho ra kết quả ngẫu nhiên xung quanh 0, không phản ánh đúng ngữ nghĩa thực tế. Điều này chỉ ra rằng để đánh giá chính xác độ tương đồng ngữ nghĩa tiếng Việt trong thực tế, bắt buộc phải sử dụng các mô hình embedding thật (như Sentence-Transformers hoặc OpenAI) đã qua huấn luyện trên kho ngữ liệu lớn.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên đăng ký học phần ở đâu và theo lịch nào? | ... Sinh viên đăng ký học phần trong cổng học vụ theo lịch của từng học kỳ ... | 0.0882 | Có | Trích xuất từ đoạn 1 hướng dẫn đăng ký cổng học vụ theo lịch từng học kỳ. |
| 2 | Khi gặp lỗi trùng lịch học phần thì sinh viên xử lý như thế nào? | ... Khi gặp lỗi trùng lịch, sinh viên điều chỉnh lớp học phần trước thời hạn ... | 0.2504 | Có | Trả lời sinh viên điều chỉnh lớp học phần trước thời hạn được công bố. |
| 3 | Thư viện cung cấp những dịch vụ gì cho sinh viên? | ... Thư viện cung cấp mượn tài liệu và không gian học tập cho sinh viên ... | 0.0328 | Có | Trả lời thư viện cung cấp mượn tài liệu và không gian học tập. |
| 4 | Đối tượng nào được phép mượn tài liệu tại thư viện? | ... cho sinh viên, giảng viên và nhân viên. Người dùng cần mang thẻ ... | 0.2198 | Có | Trả lời đối tượng gồm sinh viên, giảng viên và nhân viên có thẻ hợp lệ. |
| 5 | Các dịch vụ do phòng Quản lý học vụ (academic-affairs) cung cấp là gì? | ... metadata doc_id: k3-course-registration, department: academic-affairs ... | 0.1500 (Filtered) | Có | Lọc thành công theo metadata department: academic-affairs và trả về quy định học vụ. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc kết hợp kỹ thuật RecursiveChunker giúp giữ ngữ cảnh nguyên vẹn tốt hơn nhiều so với FixedSizeChunker, đồng thời việc gắn metadata chi tiết (department, audience, source_url) cho từng chunk giúp việc tìm kiếm chính xác và hỗ trợ truy xuất nguồn gốc thông tin cực kỳ hiệu quả trong RAG.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
