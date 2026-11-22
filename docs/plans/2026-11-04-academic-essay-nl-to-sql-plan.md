# Kế Hoạch Xây Dựng Bài Tiểu Luận Demo: Hệ Thống Multi-Agent NL-to-SQL

> **For Antigravity:** REQUIRED WORKFLOW: Use single-flow execution mode to execute this plan.

**Goal:** Xây dựng bài tiểu luận demo hoàn chỉnh dưới định dạng Word (`.docx`), độ dài chuẩn 5 chương (~10-15 trang), giải thích toàn diện hệ thống từ trực quan dễ hiểu cho người mới đến chi tiết học thuật cho giảng viên, kèm sơ đồ tư duy và kết quả thực nghiệm.

**Architecture:** Sử dụng script Python với thư viện `python-docx` trong môi trường `ai` để tạo tài liệu định dạng chuẩn học thuật (Times New Roman, bìa chuẩn, mục lục, bảng biểu có style, sơ đồ dạng khối và bảng phân rã) và lưu trực tiếp ra file Word ở thư mục gốc.

**Tech Stack:** Python 3.11, `python-docx`, `uv`.

---

### Task 1: Biên soạn kịch bản tạo tài liệu Word học thuật (`ai/src/generate_essay.py`)

**Files:**
- Create: `c:\KHDL K46\TTS\ai\src\generate_essay.py`

**Mô tả công việc:**
1. Cấu hình định dạng trang và phong cách văn bản:
   - Margin: Top 2.0cm, Bottom 2.0cm, Left 2.5cm, Right 2.0cm.
   - Font: Times New Roman, cỡ 13pt cho nội dung thường, dãn dòng 1.3 lines, space after 4pt.
   - Định dạng Headings: Heading 1 (16pt đậm, màu xanh đậm học thuật `#1F4E79`), Heading 2 (14pt đậm), Heading 3 (13pt nghiêng/đậm).
   - Định dạng bảng: header có màu nền, viền lưới thanh mảnh, căn giữa.
2. Nội dung chi tiết:
   - **Bìa chính thức**: Đầy đủ thông tin đề tài, Khoa Khoa học Dữ liệu K46.
   - **Tóm tắt (Abstract) & Danh mục thuật ngữ**: LLM, NL-to-SQL, MAC-SQL, AST, ReAct, SSE.
   - **Chương 1**: Bối cảnh tra cứu học vụ, giới hạn của Chatbot đơn lẻ (hallucination, SQL sai lệch, rủi ro bảo mật), mục tiêu đề tài.
   - **Chương 2**: Giải thích dễ hiểu cho người mới bắt đầu (bảng ẩn dụ đời thực: Kho hồ sơ, Thủ kho, Phiên dịch viên, Bảo vệ, Bếp mở), Sơ đồ tư duy dạng bảng phân rã, Lý thuyết MAC-SQL (COLING 2024), ReAct & LangGraph.
   - **Chương 3**: Lược đồ CSDL PostgreSQL (Supabase), Kiến trúc đa tác tử phân cấp (Deep Agent + SQL Query Agent), Hàng rào bảo mật (AST Guardrails chặn DROP/DELETE/UPDATE), Technical Inspector (SSE viễn trắc).
   - **Chương 4**: Triển khai thực nghiệm, phân tích 6 kịch bản demo mẫu (Học bổng, Tín chỉ, Cảnh báo học vụ GPA < 2.0, Top môn trượt, Chặn phá hoại, Câu hỏi ngoài lề), Bảng so sánh Single vs Multi-Agent.
   - **Chương 5**: Đánh giá, kết luận và hướng mở rộng tương lai.
   - **Tài liệu tham khảo**: Định dạng trích dẫn chuẩn học thuật.

---

### Task 2: Thực thi sinh tài liệu và kiểm thử chất lượng file `.docx`

**Files:**
- Output: `c:\KHDL K46\TTS\Tieu_Luan_Multi_Agent_NL_to_SQL_KHDL.docx`

**Mô tả công việc:**
1. Chạy script trong môi trường `ai`:
   ```bash
   cd c:\KHDL K46\TTS\ai
   uv run python src/generate_essay.py
   ```
2. Kiểm tra file Word tạo ra:
   - File tồn tại và có dung lượng hợp lệ (> 40 KB).
   - Kiểm tra trích xuất text XML từ file docx để đảm bảo đủ 5 chương, các bảng biểu và mục lục đều có mặt đầy đủ.

---

### Task 3: Cập nhật bảng theo dõi tiến độ (`docs/plans/task.md`)

**Files:**
- Modify: `c:\KHDL K46\TTS\docs\plans\task.md`

**Mô tả công việc:**
Cập nhật trạng thái công việc vào bảng theo quy chuẩn đơn luồng.

