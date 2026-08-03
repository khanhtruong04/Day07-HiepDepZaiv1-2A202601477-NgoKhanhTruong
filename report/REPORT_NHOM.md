# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Hiệp Đẹp Zai v1

**Thành viên:** \
Nguyễn Thị Xuân Mai - 2A202601691 \
Cao Hữu Phúc - 2A202601283 \
Trần Doãn Hưng - 2A202601143 \
Ngô Khánh Trượng - 2A202601477 \
Lê Tuấn Hiệp - 2A202601667

**Ngày:** 03/08/2026

**Tổng điểm phần nhóm: 40** = Chất lượng bộ tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Demo (5).

## Phân công công việc

| Thành viên | Mã sinh viên | Công việc phụ trách | Sản phẩm/Kết quả |
|---|---|---|---|
| Nguyễn Thị Xuân Mai | 2A202601691 | Thu thập và kiểm chứng nguồn về đăng ký môn học; làm sạch nội dung tài liệu | `course-registration.md`; đối chiếu URL, phiên bản và các mốc 14 tín chỉ |
| Cao Hữu Phúc | 2A202601283 | Thu thập tài liệu học bổng và xây dựng metadata schema | `academic-scholarship.md`, `study-abroad-scholarship.md`; rà soát `audience`, `department`, `category` |
| Trần Doãn Hưng | 2A202601143 | Hoàn thiện mã nguồn RAG, tích hợp ingest/vector store và viết chiến lược HeadingChunker | Các module trong `src/`, `HeadingChunker` và script `scripts/evaluate_group.py` |
| Ngô Khánh Trượng | 2A202601477 | Thiết kế 5 benchmark queries, gold answers và kiểm tra metadata filtering | Bộ câu hỏi đánh giá; kiểm chứng chunk nguồn và hai query có lọc `audience` |
| Lê Tuấn Hiệp | 2A202601667 | Chạy so sánh Fixed, Sentence, Recursive và Heading; tổng hợp failure analysis và nội dung demo | Bảng điểm retrieval, phân tích lỗi query học bổng 18 tín chỉ và kết luận chiến lược |

**Cách phối hợp:** Cả năm thành viên cùng rà soát corpus, chạy chung một bộ năm câu hỏi bằng local embedding và kiểm tra chéo gold answer trước khi chốt báo cáo. Trần Doãn Hưng tổng hợp thay đổi vào repo; các thành viên còn lại xác nhận nội dung thuộc phần mình phụ trách.

## 1. Lựa chọn tài liệu (10 điểm)

### Phạm vi

**Chủ đề K3:** Dịch vụ và quy định đại học.

**Phạm vi nhóm:** Quy định đăng ký học phần và các chính sách học bổng tại Trường Đại học Khoa học Tự nhiên, ĐHQGHN (HUS).

### Danh sách tài liệu

| # | Tên tài liệu | Nguồn | Ngày lấy / Phiên bản | Số ký tự | Metadata chính |
|---|---|---|---|---:|---|
| 1 | Hướng dẫn đăng ký môn học tại HUS | [Khoa Địa lý HUS](https://geography.hus.vnu.edu.vn/sinh-vien/dang-ky-mon-hoc) | 03/08/2026; không nêu phiên bản | 869 | `audience=student`, `category=course-registration` |
| 2 | Quy định học bổng khuyến khích học tập HUS | [Khoa Địa chất HUS](https://geology.hus.vnu.edu.vn/wp-content/uploads/2019/03/Quy-%C4%91%E1%BB%8Bnh-h%E1%BB%8Dc-b%E1%BB%95ng-c%C3%B3-hi%E1%BB%87u-l%E1%BB%B1c-t%E1%BB%AB-n%C4%83m-h%E1%BB%8Dc-2014-2015.pdf) | 03/08/2026; hiệu lực từ năm học 2014–2015 | 909 | `audience=student`, `category=scholarship` |
| 3 | Học bổng ngành khoa học cơ bản theo Nghị định 179 | [Khoa Sinh học HUS](https://bio.hus.vnu.edu.vn/tin-vui-cho-nguoi-hoc-khoa-sinh-hoc-chinh-phu-ban-hanh-chinh-sach-hoc-bong-cac-nganh-khoa-hoc-co-ban-theo-nghi-dinh-179/) | 03/08/2026; 179/2026/NĐ-CP | 999 | `audience=student`, `category=scholarship` |
| 4 | Học phí và học bổng trong thông tin tuyển sinh HUS 2026 | [Tuyển sinh HUS](https://tuyensinh.hus.vnu.edu.vn/DATA/TUYENSINH/IMAGES/2026/01/9.1.26-chi-tiet-du-thao_dang-cong-tuyen-sinh.pdf) | 03/08/2026; dự thảo tuyển sinh 2026 | 757 | `audience=prospective-student`, `category=admissions-scholarship` |
| 5 | Cơ hội học bổng du học của sinh viên HUS | [Khoa KTTV&HĐH HUS](https://hmo.hus.vnu.edu.vn/dao-tao/hoc-bong-du-hoc) | 03/08/2026; không nêu phiên bản | 805 | `audience=student`, `category=scholarship` |

Corpus nằm tại `data/hus_services/`; `sources.csv` ánh xạ một-một với năm tài liệu.

**Quản trị dữ liệu:**

- [x] Chỉ sử dụng trang công khai thuộc các tên miền chính thức của HUS; không chứa dữ liệu cá nhân hoặc nội dung sau đăng nhập.
- [x] Mỗi file có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language`.
- [x] Nội dung được làm sạch và diễn đạt lại từ nguồn, không tự thêm quy định.

### Metadata schema

| Trường | Kiểu | Ví dụ | Công dụng |
|---|---|---|---|
| `doc_id` | string | `hus-course-registration` | Định danh, truy vết và xóa các chunk |
| `source_url` | string | `https://geography.hus.vnu.edu.vn/...` | Kiểm chứng tại nguồn |
| `retrieved_at` | date/string | `2026-08-03` | Theo dõi độ mới |
| `document_version` | string | `179/2026/NĐ-CP` | Phân biệt phiên bản quy định |
| `audience` | string | `student` | Tách sinh viên hiện tại khỏi thí sinh |
| `department` | string | `faculty-of-biology` | Thu hẹp đơn vị phụ trách |
| `category` | string | `scholarship` | Lọc nhóm dịch vụ |
| `language` | string | `vi` | Hỗ trợ corpus đa ngôn ngữ |

## 2. Thiết kế chiến lược (15 điểm)

### Thiết lập chung

- Embedder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Mock embedding chỉ dùng cho unit test.
- Cùng corpus HUS, cùng 5 query và cùng local embedder.
- Script tái lập: `python -m scripts.evaluate_group`.

### Baseline trên corpus

Kết quả `ChunkingStrategyComparator().compare(..., chunk_size=500)` trên ba tài liệu đầu theo thứ tự nạp:

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Nhận xét |
|---|---|---:|---:|---|
| Quy định học bổng KKHT | Fixed size | 2 | 454,00 | Ít chunk nhưng có thể cắt giữa mục |
| Quy định học bổng KKHT | Sentence | 2 | 452,50 | Giữ nguyên câu |
| Quy định học bổng KKHT | Recursive | 2 | 453,00 | Giữ đoạn và điều kiện khá tốt |
| Tuyển sinh và học bổng 2026 | Fixed size | 2 | 378,00 | Đủ ngữ cảnh cho các con số |
| Tuyển sinh và học bổng 2026 | Sentence | 2 | 376,50 | Dễ đọc |
| Tuyển sinh và học bổng 2026 | Recursive | 2 | 377,00 | Giữ các mục học phí/học bổng |
| Học bổng khoa học cơ bản | Fixed size | 2 | 499,00 | Sát giới hạn 500 ký tự |
| Học bổng khoa học cơ bản | Sentence | 3 | 331,33 | Mạch lạc nhưng nhiều chunk hơn |
| Học bổng khoa học cơ bản | Recursive | 3 | 331,33 | Tách tốt theo đoạn/mục |

### Chiến lược của năm thành viên

| Thành viên | Chiến lược | Tham số/Lựa chọn | Lý do thử nghiệm |
|---|---|---|---|
| Nguyễn Thị Xuân Mai | FixedSizeChunker | `chunk_size=500`, `overlap=50` | Làm baseline đơn giản, overlap giúp giữ nội dung tại ranh giới chunk |
| Cao Hữu Phúc | SentenceChunker | `max_sentences_per_chunk=3` | Giữ nguyên ranh giới câu và làm chunk dễ đọc |
| Trần Doãn Hưng | HeadingChunker | `chunk_size=500`, recursive fallback | Khai thác cấu trúc heading của tài liệu quy định |
| Ngô Khánh Trượng | RecursiveChunker | `chunk_size=500` | Ưu tiên đoạn, dòng và câu trước khi cắt theo ký tự |
| Lê Tuấn Hiệp | Recursive + metadata filter | `chunk_size=500`, lọc `audience` | Đánh giá tác động kết hợp giữa chunking và lọc đúng đối tượng |



### So sánh định lượng

| Chiến lược | Số chunk | Điểm (/10) | Điểm mạnh | Điểm yếu |
|---|---:|---:|---|---|
| Fixed 500, overlap 50 | 11 | **10** | Ít chunk, overlap giữ đủ điều kiện | Có thể cắt không đúng cấu trúc |
| Sentence, 3 câu/chunk | 12 | 9 | Mạch lạc, dễ đọc | Query 18 tín chỉ chỉ đưa tài liệu đúng lên rank 2 |
| Recursive 500 | 11 | **10** | Cân bằng kích thước và ngữ cảnh | Không luôn giữ nguyên heading |
| Heading 500 | 18 | 9 | Giữ cấu trúc chính sách | Section ngắn làm tăng nhiễu; query 18 tín chỉ ở rank 3 |

**Kết luận:** Recursive 500 là lựa chọn mặc định tốt nhất vì đạt 10/10, giữ điều kiện trong cùng đoạn nhưng không tạo quá nhiều chunk. Fixed cũng đạt 10/10 trên năm query này, tuy nhiên Recursive an toàn hơn khi tài liệu dài và có nhiều đoạn không đều.

## 3. Câu hỏi đánh giá và chất lượng truy xuất (10 điểm)

### Năm câu hỏi chung và gold answer

| # | Query | Gold answer | Chunk chứa thông tin |
|---|---|---|---|
| 1 | Sinh viên chương trình chuẩn phải đăng ký tối thiểu bao nhiêu tín chỉ trong học kỳ chính? | Tối thiểu 14 tín chỉ; học ít hơn phải được Thủ trưởng đơn vị đào tạo đồng ý. | `hus-course-registration`, mục **Khối lượng đăng ký**; dùng `metadata_filter={"audience":"student"}` |
| 2 | Sinh viên phải học tối thiểu bao nhiêu tín chỉ để được xét học bổng khuyến khích học tập? | Tối thiểu 18 tín chỉ trong học kỳ xét, không tính các học phần được loại trừ. | `hus-academic-scholarship`, mục **Điều kiện xét** |
| 3 | Chính sách học bổng ngành khoa học cơ bản bắt đầu tính cấp từ ngày nào? | Từ 01/09/2026, áp dụng cho người tuyển sinh từ năm 2025. | `hus-basic-science-scholarship-2026`, mục **Thời điểm áp dụng** |
| 4 | Học bổng cao nhất cho sinh viên chương trình ưu tiên đầu tư năm 2026 là bao nhiêu? | 35 triệu đồng/SV/năm và có thể nhận tới 140 triệu đồng/SV. | `hus-admissions-scholarship-2026`, mục **Học bổng**; lọc `audience=prospective-student` |
| 5 | Sinh viên cần điểm trung bình bao nhiêu trong bốn học kỳ gần nhất để nộp hồ sơ học bổng du học? | Từ 8,2/10 trở lên trong bốn học kỳ gần nhất. | `hus-study-abroad-scholarship`, mục **Điều kiện tham khảo** |

### Kết quả tốt nhất (Recursive 500)

| # | Top-1 đúng? | Điểm cosine | Kết quả agent được đối chiếu với gold answer |
|---|---|---:|---|
| 1 | Có | 0,762857 | Đúng 14 tín chỉ và điều kiện xin phép |
| 2 | Có | 0,731460 | Đúng tối thiểu 18 tín chỉ |
| 3 | Có | 0,712989 | Đúng ngày 01/09/2026 và khóa tuyển từ 2025 |
| 4 | Có | 0,747856 | Đúng 35 triệu/năm và tối đa 140 triệu |
| 5 | Có | 0,720324 | Đúng ngưỡng 8,2/10 trong bốn học kỳ |

**Kết quả:** 5/5 tài liệu đúng ở top-1, câu trả lời khớp gold answer, tương ứng 10/10.

**Metadata filter:** Query 1 lọc `audience=student` để loại tài liệu tuyển sinh dành cho `prospective-student`. Query 4 dùng bộ lọc ngược lại. Với corpus nhỏ, filter không luôn thay đổi top-1 nhưng bảo đảm đúng đối tượng và tránh trộn quy định sinh viên hiện tại với quyền lợi tuyển sinh.

### Failure analysis

Query 2 là failure case của Sentence và Heading. Cả hai xếp tài liệu học bổng du học ở trên quy định học bổng khuyến khích học tập vì cùng chứa nhiều từ “sinh viên”, “học bổng”, “học tập”; tài liệu đúng chỉ ở rank 2 hoặc rank 3. Recursive giữ cụm điều kiện “tối thiểu 18 tín chỉ” trong một chunk đủ ngữ cảnh và đưa tài liệu đúng lên top-1 với điểm 0,731460.

Có thể cải thiện Heading bằng cách gắn tiêu đề tài liệu vào mọi section, lọc thêm `category=scholarship`, hoặc rerank theo các cụm số liệu trong query. Failure này cũng cho thấy chunk ngắn, rõ cấu trúc chưa chắc tốt nếu mất bối cảnh cấp tài liệu.

## 4. Demo và bài học nhóm (5 điểm)

### Ba insight chính

- Cùng corpus và embedding, Recursive/Fixed đạt 10/10 còn Sentence/Heading đạt 9/10; ranh giới chunk ảnh hưởng trực tiếp đến thứ hạng.
- Điểm cosine cao không tự bảo đảm đúng quy định: các tài liệu học bổng có vốn từ giống nhau nên dễ cạnh tranh sai.
- `audience` là metadata nghiệp vụ quan trọng để tách sinh viên hiện tại khỏi thí sinh tuyển sinh.

**Bài học:** Không có chiến lược chunking tốt nhất cho mọi corpus. Trên bộ tài liệu HUS, Heading tạo nhiều section ngắn và làm mất một phần bối cảnh cấp tài liệu; Recursive cân bằng cấu trúc và ngữ cảnh tốt hơn.

**Nếu làm lại:** Nhóm sẽ xác minh định kỳ các tài liệu cũ, bổ sung `effective_from`, `effective_to` và trạng thái `draft/final`, đồng thời mở rộng benchmark để đo Recall@3 và MRR. Đặc biệt, tài liệu học bổng hiệu lực từ 2014–2015 và dự thảo tuyển sinh 2026 cần được gắn phiên bản rõ ràng trước khi dùng trong hệ thống thật.

### Khả năng tái lập

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
python -m scripts.evaluate_group
```

## Tự đánh giá

| Tiêu chí | Điểm |
|---|---:|
| Lựa chọn tài liệu | 10 / 10 |
| Thiết kế chiến lược | 15 / 15 |
| Chất lượng truy xuất | 10 / 10 |
| Demo | 5 / 5 |
| **Tổng** | **40 / 40** |
