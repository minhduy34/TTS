# Thiết Kế Bài Tiểu Luận Demo: Hệ Thống Multi-Agent Tra Cứu Dữ Liệu Học Vụ (NL-to-SQL)

- **Đề tài**: Hệ Thống Multi-Agent Hỗ Trợ Tra Cứu Dữ Liệu Học Vụ Bằng Kỹ Thuật NL-to-SQL
- **Dự án**: TTS — KHDL K46
- **Ngày lập**: 04/11/2026
- **Trạng thái**: Đã được phê duyệt bởi người dùng

---

## 1. Mục Tiêu & Yêu Cầu

1. **Đối tượng độc giả đa dạng**:
   - Vừa đáp ứng tính chuẩn tắc học thuật cho giảng viên đánh giá (đủ 5 chương, cơ sở lý thuyết MAC-SQL COLING 2024, LangGraph, PostgreSQL, Guardrails, Technical Inspector).
   - Vừa giải thích trực quan, dễ hiểu từ con số 0 cho người chưa biết gì về kỹ thuật thông qua các hình ảnh ẩn dụ (văn phòng một cửa, thủ kho, người phiên dịch, nhóm chuyên viên, nhà bếp mở).
   - Đi kèm sơ đồ tư duy (Mindmap) và sơ đồ luồng hoạt động (Workflow Flowchart) từng bước.
2. **Hình thức xuất bản**:
   - File tài liệu Word (`.docx`) chuẩn mẫu tiểu luận đại học (Trang bìa trang trọng, Mục lục, Danh mục bảng biểu/thuật ngữ, Font Times New Roman 12-13pt, dãn dòng 1.3-1.5, lề chuẩn, bảng biểu có style đồng nhất).
   - Tên file dự kiến: `Tieu_Luan_Multi_Agent_NL_to_SQL_KHDL.docx`.
3. **Quy mô**:
   - Khung tiểu luận demo chuẩn 5 chương (~10-15 trang), nội dung cô đọng súc tích, bao quát toàn bộ mã nguồn và dữ liệu thực tế trong dự án.

---

## 2. Bố Cục Chi Tiết 5 Chương

### Trang Bìa & Đầu mục
- Bìa chính quy: Tên trường/khoa, Tên đề tài tiếng Việt & tiếng Anh, Giảng viên hướng dẫn, Nhóm sinh viên thực hiện (KHDL K46), Thời gian.
- Lời nói đầu & Tóm tắt đề tài (Abstract).
- Mục lục tổng hợp.
- Danh mục thuật ngữ & từ viết tắt: LLM, NL-to-SQL, ReAct, AST, SSE, Multi-Agent.

### Chương 1: Giới Thiệu & Đặt Vấn Đề
- 1.1. Bối cảnh số hóa giáo dục đại học và nhu cầu tra cứu học vụ của sinh viên.
- 1.2. Thách thức cốt lõi: Khoảng cách giữa ngôn ngữ tự nhiên và cơ sở dữ liệu quan hệ; hạn chế của Chatbot Single-Agent (ảo giác dữ liệu, sinh sai SQL, rủi ro an ninh dữ liệu).
- 1.3. Mục tiêu, phạm vi và những đóng góp cốt lõi của đề tài.

### Chương 2: Giải Thích Dễ Hiểu & Cơ Sở Khoa Học
- 2.1. Giải thích hệ thống cho người mới bắt đầu (Bảng ẩn dụ đời thực: Kho hồ sơ, Thủ kho, Phiên dịch viên, Bảo vệ, Bếp mở).
- 2.2. Sơ đồ tư duy (Mindmap) phân rã các thành phần công nghệ.
- 2.3. Cơ sở lý thuyết học thuật:
  - Khung cộng tác đa tác tử MAC-SQL (COLING 2024).
  - Phương pháp suy luận ReAct (Reasoning + Acting).
  - Điều phối đồ thị trạng thái với LangGraph.

### Chương 3: Phân Tích & Thiết Kế Kiến Trúc Hệ Thống
- 3.1. Thiết kế cơ sở dữ liệu học vụ PostgreSQL (Supabase) và mô hình dữ liệu (Students, Courses, Enrollments, Scholarships, Lecturers, Classes).
- 3.2. Kiến trúc Multi-Agent phân cấp:
  - Deep Agent (Điều phối luồng, phân loại ý định, lọc câu hỏi ngoài lề).
  - SQL Query Agent (ReAct Agent đọc schema, sinh câu lệnh SQL).
- 3.3. Hàng rào an toàn kép (Dual Guardrails):
  - Kiểm duyệt cây cú pháp trừu tượng (AST Parser) chặn lệnh phá hoại (`DROP`, `DELETE`, `UPDATE`, `INSERT`).
  - Cưỡng chế kết nối Read-Only ở tầng Database.
- 3.4. Bảng điều khiển viễn trắc minh bạch kỹ thuật (Technical Inspector):
  - Luồng truyền dữ liệu thời gian thực Server-Sent Events (SSE).
  - Hiển thị song song: Nhật ký thực thi, Câu lệnh SQL thô, Bảng dữ liệu gốc và độ trễ mili-giây.

### Chương 4: Thực Nghiệm, 6 Kịch Bản Demo & Đánh Giá
- 4.1. Môi trường triển khai kỹ thuật (Python 3.11, uv, FastAPI, Gemini API, Supabase).
- 4.2. Trình diễn 6 kịch bản thực nghiệm (Preset 1-Click):
  - Hồi 1 (Sinh viên): Tra cứu học bổng, tính toán tín chỉ tích lũy.
  - Hồi 2 (Cố vấn): Cảnh báo học vụ GPA < 2.0, thống kê môn học trượt nhiều nhất.
  - Hồi 3 (An toàn & Ngoại lệ): Chặn phá hoại SQL Injection và xử lý câu hỏi ngoài phạm vi.
- 4.3. Đánh giá kết quả thực nghiệm: So sánh Single-Agent vs Multi-Agent về độ chính xác logic, khả năng tự sửa lỗi và tính minh bạch.

### Chương 5: Kết Luận & Hướng Phát Triển
- 5.1. Tổng kết kết quả đạt được của dự án.
- 5.2. Các hạn chế tồn đọng và hướng mở rộng (Fine-tuning mô hình ngôn ngữ tiếng Việt chuyên biệt, Semantic Caching để giảm chi phí API, hỗ trợ giọng nói đa phương ngữ).

### Tài Liệu Tham Khảo (References)
- Bài báo MAC-SQL (Wang et al., COLING 2024).
- Tài liệu kỹ thuật LangGraph, LangChain, Google Gemini, PostgreSQL.

---

## 3. Kỹ Thuật Tạo File .docx
- Sử dụng môi trường `ai` (đã có sẵn `python-docx`).
- Viết kịch bản Python `generate_essay.py` để định dạng chính xác từng thành phần:
  - Kiểu chữ Times New Roman, cỡ 13pt nội dung, 14-16pt tiêu đề.
  - Dãn dòng 1.3, khoảng cách đoạn `space_after = Pt(6)`.
  - Bảng biểu có viền kẻ tinh tế, màu nền tiêu đề xanh than trang trọng (`#1F4E79`).
  - Sơ đồ khối trực quan được format rõ ràng, căn lề trung tâm.

