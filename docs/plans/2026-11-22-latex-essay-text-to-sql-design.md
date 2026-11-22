# Thiết Kế Tiểu Luận Học Thuật LaTeX: Xây Dựng Hệ Thống Text-to-SQL Hỗ Trợ Truy Vấn Dữ Liệu

**Ngày thiết kế:** 2026-11-22
**Đề tài:** Xây dựng Hệ thống Text-to-SQL Hỗ trợ Truy vấn Dữ liệu
**Sinh viên thực hiện:** Cái Minh Duy — **MSSV:** 4654110003
**Học phần:** Xử lý Ngôn ngữ Tự nhiên (NLP) — **GVHD:** TS. Lê Quang Hùng
**Ngành - Khóa:** Khoa học Dữ liệu - Khóa K46 (Trường Đại học Quy Nhơn - Khoa Toán và Thống kê)

---

## 1. Mục tiêu & Phạm vi

Xây dựng bộ mã nguồn LaTeX hoàn chỉnh, chuẩn học thuật cho bài tiểu luận **"XÂY DỰNG HỆ THỐNG TEXT-TO-SQL HỖ TRỢ TRUY VẤN DỮ LIỆU"**, đáp ứng đầy đủ các yêu cầu:
1. **Trang bìa chuẩn mẫu `report/bìa.docx`:** Tái tạo khung viền đôi, quốc hiệu/tên trường, logo Trường Đại học Quy Nhơn (`figures/logo_qnu.png` trích xuất từ `report/bìa.docx`) và thông tin sinh viên `Cái Minh Duy` (`4654110003`), học phần `Xử lý Ngôn ngữ Tự nhiên (NLP)`, GVHD `TS. Lê Quang Hùng`.
2. **Cấu trúc 5 chương + Tóm tắt theo đề cương chuẩn:** Tóm tắt (Abstract), Chương 1 (Giới thiệu), Chương 2 (Cơ sở lý thuyết & Nghiên cứu liên quan), Chương 3 (Phương pháp đề xuất & Kiến trúc hệ thống), Chương 4 (Thực nghiệm & Đánh giá), Chương 5 (Kết luận & Hướng phát triển) và Tài liệu tham khảo.
3. **Kết hợp chặt chẽ 2 bài báo khoa học & Source code thực tế:**
   - Bài báo 1 (`report/2312.11242v6.pdf`): *MAC-SQL: A Multi-Agent Collaborative Framework for Text-to-SQL* (Wang et al., COLING 2024 / arXiv 2025) — nền tảng lý thuyết 3 tác tử Selector, Decomposer, Refiner và các công thức xác suất sinh truy vấn.
   - Bài báo 2 (`report/2507.14372v1.pdf`): *Text-to-SQL for Enterprise Data Analytics* (Chen et al., LinkedIn, KDD '25) — nền tảng làm giàu ngữ nghĩa lược đồ (Table/Column Descriptions), định tuyến ý định (Intent Classifier), sửa lỗi ảo giác lược đồ và bộ độ đo thực tế.
   - Source code thực tế của dự án (`fe_be/schema.sql`, `fe_be/seed.py`, `ai/src/`): Cơ sở dữ liệu PostgreSQL (Supabase) mô hình hình sao (Star Schema) 8 bảng học vụ với 2.769 bản ghi, chú thích ngữ nghĩa tiếng Việt (`COMMENT ON TABLE/COLUMN`), hệ thống đa tác tử LangGraph (`Deep Agent` + `SQL Query Agent`) sử dụng `gemini-3.5-flash-lite` (`temperature = 0`), cơ chế `ThreadedConnectionPool`, `_SCHEMA_CACHE` và rào chắn bảo mật Read-Only.
4. **Hệ thống Hình ảnh minh họa, Công thức Toán học & Bảng biểu:**
   - Trích xuất hình ảnh gốc từ `bìa.docx` và 2 bài báo PDF (`2312.11242v6.pdf`, `2507.14372v1.pdf`).
   - Vẽ sơ đồ vector chất lượng cao bằng **TikZ / pgfplots** (Sơ đồ ERD Star Schema 8 bảng, Sơ đồ Pipeline Hệ thống Đa tác tử LangGraph, Biểu đồ cột Ablation Study EX/EM theo 4 độ khó, Biểu đồ phân tích lỗi).

---

## 2. Kiến trúc Thư mục Đầu ra

Phương án đã chọn: **Phương án 1 — Cấu trúc LaTeX nguyên khối tự chứa trong `report/`**:

```text
report/
├── main.tex                         # Tệp LaTeX chính (Trang bìa, Tóm tắt, Mục lục, Danh mục hình/bảng, Chương 1–5)
├── references.bib                   # Cơ sở dữ liệu tài liệu tham khảo chuẩn BibTeX
└── figures/                         # Thư mục chứa hình ảnh minh họa
    ├── logo_qnu.png                 # Logo ĐH Quy Nhơn trích xuất từ word/media/image1.png của bìa.docx
    ├── mac_sql_framework.png        # Hình kiến trúc tổng thể MAC-SQL (trích xuất từ trang 2 của 2312.11242v6.pdf)
    ├── mac_sql_agents.png           # Hình minh họa Decomposer & Refiner (trích xuất từ trang 4 của 2312.11242v6.pdf)
    ├── linkedin_kg_agent.png        # Hình Knowledge Graph & Query Writer Agent (trích xuất từ trang 2-3 của 2507.14372v1.pdf)
    └── ui_technical_inspector.png   # Hình minh họa giao diện thực nghiệm của hệ thống
```

---

## 3. Thiết kế Chi tiết Từng Phần trong `report/main.tex`

### 3.1. Cấu hình Kỹ thuật LaTeX (Preamble)
- `\documentclass[12pt,a4paper]{report}` với `geometry` (`left=3cm, right=2cm, top=2.5cm, bottom=2.5cm`).
- Tiếng Việt chuẩn UTF-8: `\usepackage[utf8]{inputenc}`, `\usepackage[T5]{fontenc}`, `\usepackage[vietnamese]{babel}`.
- Toán học & Giải thuật: `amsmath`, `amssymb`, `amsfonts`, `mathtools`, `algorithm`, `algpseudocode`.
- Bảng biểu & Mã nguồn: `booktabs`, `longtable`, `array`, `multirow`, `tabularx`, `listings`, `xcolor`.
- Đồ họa & Biểu đồ: `graphicx`, `tikz`, `pgfplots` (với các thư viện `shapes.geometric`, `arrows.meta`, `positioning`, `calc`, `fit`, `backgrounds`), `subcaption`, `float`.
- Liên kết & Trích dẫn: `hyperref`, `cite`.

### 3.2. Tóm tắt (Abstract)
- Trình bày 4 ý cốt lõi theo đề cương: **Bối cảnh & Vấn đề**, **Phương pháp đề xuất**, **Thực nghiệm & Độ đo**, **Kết quả chính** cùng danh mục **Từ khóa (Keywords)**.

### 3.3. Chương 1: Giới thiệu (Introduction)
- **1.1. Bối cảnh và Đặt vấn đề:** Nhu cầu khai thác dữ liệu học vụ (sinh viên, học phần, đăng ký học phần, điểm số, tiến độ tích lũy tín chỉ, học bổng) và rào cản của ngôn ngữ truy vấn SQL đối với người dùng không chuyên.
- **1.2. Các thách thức cốt lõi của bài toán Text-to-SQL:**
  - *Sự nhập nhằng của ngôn ngữ tự nhiên tiếng Việt:* Từ đồng nghĩa ("rớt môn" $\leftrightarrow$ `status = 'failed'`, "đang học" $\leftrightarrow$ `status = 'active'` / `'in_progress'`), quy chiếu thời gian tương đối ("học kỳ này", "năm học trước").
  - *Liên kết lược đồ (Schema Linking) & Ảo giác (Hallucination):* Ánh xạ thực thể sang bảng/cột và khóa ngoại trên lược đồ hình sao đa bảng; dẫn chứng nghiên cứu từ bài báo LinkedIn (`2507.14372v1.pdf`) và MAC-SQL (`2312.11242v6.pdf`).
  - *Tính đúng đắn khi thực thi & An toàn dữ liệu:* Khác biệt giữa đúng cú pháp và đúng logic nghiệp vụ; nguy cơ lệnh phá hủy dữ liệu (`DROP`, `DELETE`, `UPDATE`).
- **1.3. Mục tiêu và Đóng góp của đề tài:**
  - Chuẩn hóa CSDL học vụ Star Schema 8 bảng trên PostgreSQL/Supabase kèm chú thích ngữ nghĩa tiếng Việt (`COMMENT ON TABLE/COLUMN`).
  - Triển khai kiến trúc đa tác tử trên LangGraph kết hợp Gemini (`temperature = 0`) theo tư tưởng MAC-SQL (*Selector*, *Decomposer*, *Refiner*).
  - Xây dựng bộ dữ liệu kiểm thử 60 câu hỏi theo 4 mức độ khó (*Easy, Medium, Hard, Extra Hard*) và thực hiện Ablation Study, Error Analysis.

### 3.4. Chương 2: Cơ sở Lý thuyết và Nghiên cứu Liên quan (Background & Related Work)
- **2.1. Định nghĩa bài toán Text-to-SQL và Các bộ dữ liệu chuẩn:**
  - Phát biểu ánh xạ hàm $f(\mathcal{Q}, \mathcal{S}, \mathcal{K}) \rightarrow \mathcal{Y}$ và mô hình hóa xác suất sinh chuỗi token tự hồi quy:
    $$P_{\mathcal{M}}(\mathcal{Y} \mid \mathcal{X}) = \prod_{i=1}^{|\mathcal{Y}|} P_{\mathcal{M}}(\mathcal{Y}_i \mid \mathcal{Y}_{<i}; \mathcal{X})$$
  - Phân tích & lập bảng so sánh các bộ dữ liệu benchmark kinh điển: **WikiSQL** (Zhong et al., 2017) [1], **Spider** (Yu et al., 2018) [2], **BIRD** (Li et al., 2023) [3], và **Spider 2.0 / Enterprise Benchmark** (Chen et al., 2025) [8].
- **2.2. Các hướng tiếp cận tiêu biểu:**
  - *Giai đoạn mạng nơ-ron và biểu diễn đồ thị:* Encoder-Decoder truyền thống, AST-based decoding và **RAT-SQL** (Wang et al., 2020) [4].
  - *Giai đoạn Mô hình ngôn ngữ lớn (LLM) và Prompt Engineering:* **DIN-SQL** (Pourreza & Rafiei, 2023) [5], **DAIL-SQL** (Gao et al., 2023) [6].
  - *Giai đoạn Kiến trúc Đa tác tử (Multi-Agent Framework):*
    - **MAC-SQL** (Wang et al., 2024/2025) [7] với các phương trình toán học cho 3 tác tử:
      - Selector: $\mathcal{S}' = f_{\text{selector}}(\mathcal{Q}, \mathcal{S}, \mathcal{K} \mid \mathcal{M})$
      - Decomposer: $P_{\mathcal{M}}(\mathcal{Y} \mid \mathcal{Q}, \mathcal{S}', \mathcal{K}) = \prod_{j=1}^{L} P_{\mathcal{M}}(\mathcal{Y}^j \mid \mathcal{Y}^{<j}; \mathcal{Q}^j, \mathcal{S}', \mathcal{K})$
      - Refiner: $\mathcal{Y} = f_{\text{refiner}}(\mathcal{E}, \mathcal{Y}', \mathcal{Q}, \mathcal{S}', \mathcal{K} \mid \mathcal{M})$
    - **LinkedIn Enterprise Text-to-SQL** (Chen et al., 2025) [8]: Đồ thị tri thức siêu dữ liệu (Knowledge Graph), phân loại ý định (Intent Classifier) và tác tử sửa lỗi ảo giác (Query Fixer & Researcher Agent).

### 3.5. Chương 3: Phương pháp Đề xuất và Kiến trúc Hệ thống (Methodology)
- **3.1. Thiết kế và chuẩn hóa Cơ sở dữ liệu Học vụ:**
  - Sơ đồ ERD mô hình hình sao (Star Schema) vẽ bằng TikZ và bảng đặc tả chi tiết 8 bảng trong `fe_be/schema.sql`: `dim_major`, `dim_department`, `dim_semester`, `dim_student`, `dim_course`, `dim_scholarship`, `fact_enrollment`, `fact_scholarship_award` (tổng cộng 2.769 bản ghi từ `fe_be/seed.py`).
  - Kỹ thuật bổ sung mô tả ngữ nghĩa (**Schema Annotation / Comments**) và truy vấn trích xuất động siêu dữ liệu qua `information_schema` & `pg_class` (`obj_description`, `col_description`) kết hợp bộ nhớ đệm `_SCHEMA_CACHE` và `ThreadedConnectionPool` trong `ai/src/agent/tools/sql_tools.py`.
- **3.2. Kiến trúc tổng thể hệ thống (System Pipeline):**
  - Sơ đồ khối TikZ luồng dữ liệu toàn trình và Giải thuật phối hợp đa tác tử (`Algorithm 1`).
  - **Tác tử điều phối & chuẩn hóa thời gian (`Deep Agent`):** Phân loại ý định (`out_of_scope_reply`), chuẩn hóa biểu thức thời gian (`resolve_time_range`) và gọi `call_sql_agent`.
  - **Thành phần 1: Tác tử trích xuất và chọn lọc lược đồ (`Selector / get_schema`):** Cung cấp siêu dữ liệu kèm chú thích tiếng Việt và ánh xạ khóa ngoại `[FK: → ...]` để tác tử chọn đúng tập bảng $\mathcal{T}'$ và cột $\mathcal{C}'$.
  - **Thành phần 2: Tác tử phân rã và sinh mã (`Decomposer & Generator` trong `SQL Query Agent`):** Áp dụng suy luận chuỗi tư duy (Chain-of-Thought) theo quy trình 5 bước bắt buộc trong `sql_query_agent.py`.
  - **Thành phần 3: Tác tử thực thi, kiểm duyệt bảo mật và tinh chỉnh (`Refiner / execute_sql`):** Rào chắn bảo mật kép (chặn đa câu lệnh `;`, chỉ cho phép `SELECT`/`WITH`, phiên `readonly=True`, `statement_timeout = '10s'`) và vòng lặp tự sửa lỗi tối đa 3 lần khi gặp lỗi cú pháp PostgreSQL hoặc kết quả rỗng bất thường.

### 3.6. Chương 4: Thực nghiệm và Đánh giá (Experiments & Results)
- **4.1. Thiết lập thực nghiệm:**
  - Phân bố tập dữ liệu kiểm thử **60 câu hỏi – SQL chuẩn** theo 4 mức độ khó của Spider: *Easy* (15 câu, 25%), *Medium* (20 câu, 33.3%), *Hard* (15 câu, 25%), *Extra Hard* (10 câu, 16.7%).
  - Cấu hình kỹ thuật: `gemini-3.5-flash-lite` (`temperature = 0`), Python 3.11, LangGraph, FastAPI SSE, PostgreSQL 15 (Supabase).
- **4.2. Độ đo đánh giá (Evaluation Metrics):**
  - Công thức và định nghĩa chi tiết của **Exact Set Match (EM)**, **Execution Accuracy (EX)**, **Valid Efficiency / Latency** và **Compilation Success Rate**.
- **4.3. Kết quả thực nghiệm và Thảo luận:**
  - **Bảng & Biểu đồ Ablation Study (`pgfplots`):** So sánh *Baseline (Zero-shot)*, *Baseline + Schema Selector/Annotation*, và *Full Pipeline (Selector + Decomposer + Refiner)* trên 4 mức độ khó, đồng thời đối chiếu với kết quả trong bài báo MAC-SQL và LinkedIn Text-to-SQL.
  - **Hiệu năng tối ưu hóa hệ thống:** So sánh độ trễ trước và sau khi áp dụng `ThreadedConnectionPool` + `_SCHEMA_CACHE` (giảm thời gian đọc schema từ `1.2s` xuống `0.0008s`).
  - **Phân tích lỗi (Error Analysis):** Bảng phân loại các nhóm lỗi phổ biến (lỗi ngữ nghĩa tiếng Việt & thang điểm, lỗi điều kiện `JOIN` khóa tự nhiên vs khóa thay thế, lỗi định dạng ngày tháng/chuỗi trạng thái) kèm ví dụ câu hỏi, SQL lỗi và SQL sau khi sửa.

### 3.7. Chương 5: Kết luận và Hướng phát triển (Conclusion & Future Work)
- **5.1. Kết luận:** Tổng kết các kết quả lý thuyết và thực nghiệm đạt được.
- **5.2. Hạn chế và Hướng phát triển:** Phân tích hạn chế về độ trễ tuần tự, chi phí token, lỗi ngữ nghĩa câm (silent semantic errors) và đề xuất 3 hướng phát triển: RAG tra cứu cell values, Knowledge Graph & Query Log Indexing (theo bài báo LinkedIn), và Fine-tuning mô hình mã nguồn mở nhỏ (theo hướng SQL-Llama 7B trong bài báo MAC-SQL).
