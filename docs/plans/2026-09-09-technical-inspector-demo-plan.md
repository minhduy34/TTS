# Technical Inspector Demo Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Xây dựng giao diện Split-View phong cách Data Science Technical Inspector (trái: Chat & 6 Preset Buttons 1-Click; phải: Live Pipeline Logs, Raw Generated SQL, Bảng dữ liệu thô PostgreSQL và Performance Metrics) để demo thuyết phục trước giáo viên KHDL.

**Architecture:** Mở rộng `call_sql_agent` trong AI Service (`ai/`) để thu thập `raw_data` từ tool `execute_sql` và gửi kèm trong SSE `done` event. Nâng cấp giao diện Web (`fe_be/frontend/`) sang dạng Split-View với bảng hiển thị dữ liệu thô và các nút bấm kịch bản sẵn có dữ liệu thật.

**Tech Stack:** Python 3.13+, FastAPI, LangGraph, psycopg2, Vanilla JS, CSS Grid/Flexbox, DOMPurify, Marked.js.

---

### Task 1: Mở rộng `call_sql_agent` để trích xuất dữ liệu bảng thô (`raw_data`)

**Files:**
- Modify: `ai/src/agent/tools/agent_tools.py:40-65`
- Test: `ai/tests/test_agent_tools.py`

**Step 1: Cập nhật kiểm thử trong `test_agent_tools.py`**
Thêm test case kiểm tra `call_sql_agent` trả về trường `raw_data` khi `execute_sql` được thực thi.

**Step 2: Chạy test để xác nhận fail**
Chạy: `uv run pytest tests/test_agent_tools.py -k test_call_sql_agent`
Kỳ vọng: FAIL vì chưa trả về `raw_data`.

**Step 3: Cập nhật mã nguồn `ai/src/agent/tools/agent_tools.py`**
Trích xuất `raw_data` từ `ToolMessage` của `execute_sql` (dạng dict chứa `rows`, `row_count`). Trả về dict: `{"answer": ..., "reasoning": ..., "sql_query": ..., "raw_data": ...}`.

**Step 4: Chạy test để xác nhận pass**
Chạy: `uv run pytest tests/test_agent_tools.py`
Kỳ vọng: PASS.

---

### Task 2: Cập nhật SSE Streaming trong `ai/src/main.py` để truyền `raw_data` và `execution_time_ms`

**Files:**
- Modify: `ai/src/main.py:90-130`
- Test: `ai/tests/test_main.py`

**Step 1: Cập nhật kiểm thử trong `test_main.py`**
Kiểm tra payload của sự kiện `done` chứa `raw_data` và `execution_time_ms`.

**Step 2: Cập nhật mã nguồn `ai/src/main.py`**
- Đo thời gian bắt đầu `start_time = time.perf_counter()`.
- Gửi `raw_data` và `execution_time_ms` vào payload của sự kiện `event: done`.

**Step 3: Chạy toàn bộ test trong `ai`**
Chạy: `uv run pytest`
Kỳ vọng: Toàn bộ test của `ai` đều PASS.

---

### Task 3: Tái cấu trúc Giao diện Split-View (`fe_be/frontend/index.html`)

**Files:**
- Modify: `fe_be/frontend/index.html`

**Step 1: Tạo cấu trúc 2 cột trong `index.html`**
- Cột trái `.left-panel`:
  - Header & Thanh Preset Chips (6 nút: SV Học bổng, SV Tín chỉ, QL Cảnh báo, QL Môn trượt, AI Ngoài lề, An toàn Chặn xóa).
  - Khung Chat và ô nhập Terminal.
- Cột phải `.right-panel` (Technical Inspector):
  - Khung Live Steps Badge (nhật ký gọi agent theo thời gian thực).
  - Khung SQL Box (dark codeblock với nút Sao chép SQL).
  - Khung Raw Data Table (bảng HTML kẻ lưới cho PostgreSQL rows).
  - Khung Performance Metrics (thời gian phản hồi, số dòng).

---

### Task 4: Cài đặt CSS phong cách Data Science Inspector (`fe_be/frontend/style.css`)

**Files:**
- Modify: `fe_be/frontend/style.css`

**Step 1: Viết CSS Split-View hiện đại, kỹ thuật**
- Bố cục Grid 2 cột responsive (`minmax(400px, 1fr) minmax(450px, 1.2fr)`).
- Preset chips với hiệu ứng hover và badge màu theo vai trò (Xanh dương cho Sinh viên, Vàng cho Cố vấn, Đỏ cho Guardrails).
- Syntax-highlighted code block và bảng dữ liệu thô với header xám đậm, sọc ngựa vằn (zebra striping) dễ đọc.

---

### Task 5: Cài đặt Logic Hiển thị Kỹ thuật (`fe_be/frontend/app.js`)

**Files:**
- Modify: `fe_be/frontend/app.js`

**Step 1: Thêm sự kiện click cho 6 Preset Chips**
Bấm chip sẽ tự động điền câu hỏi tương ứng và kích hoạt gửi request.

**Step 2: Cập nhật hàm lắng nghe SSE**
- `es.addEventListener("status", ...)`: Render bước thực thi vào Live Steps Badge ở cột phải.
- `es.addEventListener("done", ...)`:
  - Cập nhật câu trả lời vào hội thoại bên trái.
  - Cập nhật câu lệnh SQL vào SQL Box bên phải.
  - Parse `raw_data.rows` và vẽ động thẻ `<table>` hiển thị các dòng dữ liệu từ Supabase.
  - Cập nhật thời gian phản hồi (ms) và số dòng dữ liệu.

---

### Task 6: Kiểm Thử Toàn Diện 6 Kịch Bản Demo (End-to-End Verification)

**Files:**
- Test: `fe_be/tests/test_main.py`
- Integration: Chạy trực tiếp trên trình duyệt `http://localhost:8000`

**Step 1: Chạy pytest cả 2 service**
- `cd ai && uv run pytest`
- `cd fe_be && uv run pytest`

**Step 2: Khởi động lại service và kiểm tra 6 Preset câu hỏi**
1. Nút 1 (SV Học bổng): Kiểm tra Vũ Dương HK1-2025-2026 và bảng raw data.
2. Nút 2 (SV Tín chỉ): Kiểm tra Quang Thị Đặng 42/125 tín chỉ.
3. Nút 3 (QL Cảnh báo): Kiểm tra bảng danh sách sinh viên GPA < 2.0.
4. Nút 4 (QL Môn trượt): Kiểm tra bảng Top 3 môn học bị trượt nhiều nhất.
5. Nút 5 (AI Ngoài lề): Kiểm tra phản hồi từ chối lịch sự, không sinh SQL.
6. Nút 6 (An toàn Chặn xóa): Kiểm tra chặn xóa, thông báo vi phạm an toàn.
