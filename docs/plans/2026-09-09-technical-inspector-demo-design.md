# Thiết Kế Hệ Thống Demo Kỹ Thuật (Data Science Technical Inspector) Cho Giáo Viên

- **Dự án**: TTS — Trợ lý AI Quản Lý Sinh Viên (KHDL K46)
- **Ngày lập**: 09/09/2026
- **Trạng thái**: Đã được phê duyệt bởi người dùng

---

## 1. Mục Tiêu & Bối Cảnh
Dự án được xây dựng phục vụ đánh giá chuyên môn bởi giảng viên ngành Khoa học Dữ liệu (KHDL). Thay vì một giao diện chat phổ thông ẩn giấu kỹ thuật, hệ thống chuyển sang phong cách **Data Science Technical Inspector (Split-View)**:
- Thể hiện sự "thô và chất" về mặt kỹ thuật: Trình diễn trực quan câu lệnh SQL được sinh ra, bảng kết quả thô từ PostgreSQL, log thực thi Agent theo thời gian thực và các chỉ số hiệu năng (latency, rows).
- Cung cấp kịch bản demo 3 hồi mạch lạc thông qua thanh Preset 1-Click, giúp buổi báo cáo trơn tru và thuyết phục.

---

## 2. Kiến Trúc Giao Diện (Split-View Layout)

Màn hình được chia đôi thành 2 cột với tỷ lệ cân đối (50% - 50% hoặc 45% - 55% trên màn hình desktop):

```
+---------------------------------------------+----------------------------------------------+
| CỘT TRÁI: QUERY CONSOLE & KỊCH BẢN DEMO     | CỘT PHẢI: TECHNICAL DATA SCIENCE INSPECTOR   |
+---------------------------------------------+----------------------------------------------+
| 1. Thanh Preset câu hỏi mẫu (1-Click Chips):| 1. Live Pipeline Execution Steps:            |
|    [SV: Học bổng] [SV: Tín chỉ]             |    - [09:15:01] Deep Agent: Phân tích ý định |
|    [QL: Cảnh báo] [QL: Môn trượt]           |    - [09:15:02] Tool: call_sql_agent         |
|    [AI: Ngoài lề] [An toàn: Chặn Xóa]       |    - [09:15:03] Schema: Đọc metadata         |
|                                             |    - [09:15:04] Executing SQL (120ms)...     |
| 2. Khung hội thoại & Input Terminal:        |                                              |
|    - Lịch sử hỏi đáp giữa User và Agent     | 2. Raw Generated SQL (Dark Codebox + Copy):  |
|    - Câu trả lời tổng hợp ngôn ngữ tự nhiên |    SELECT s.full_name, AVG(e.grade)...       |
|    - Ô nhập câu hỏi thủ công                |                                              |
|                                             | 3. Raw PostgreSQL Data Table:                |
|                                             |    +---------+-----------+-------+           |
|                                             |    | Mã SV   | Họ tên    | Điểm  |           |
|                                             |    +---------+-----------+-------+           |
|                                             |    | SV2021  | Nguyễn A  | 8.5   |           |
|                                             |                                              |
|                                             | 4. Metrics & Performance:                    |
|                                             |    - Latency: 1.25s | Số dòng: 5 dòng        |
+---------------------------------------------+----------------------------------------------+
```

---

## 3. Luồng Dữ Liệu Kỹ Thuật (Data Flow & Backend Modifications)

### 3.1. Nâng cấp `ai/src/agent/tools/agent_tools.py`
- Khi `call_sql_agent` gọi SQL Agent thực thi công cụ `execute_sql`, lưu lại không chỉ câu lệnh `sql_query` mà cả kết quả thô `raw_data` gồm:
  - `columns`: Danh sách tên các cột.
  - `rows`: Mảng các bản ghi dữ liệu trả về từ Supabase.
  - `row_count`: Số lượng dòng.
- Trả về cấu trúc: `{"answer": ..., "reasoning": ..., "sql_query": ..., "raw_data": ...}`.

### 3.2. Nâng cấp SSE stream tại `ai/src/main.py`
- Bổ sung trường `raw_data` và `execution_time_ms` vào sự kiện `event: done`.
- Gửi các sự kiện `event: status` chi tiết kèm bước thực thi để cột Inspector render timeline theo thời gian thực.

---

## 4. Bảng Điều Khiển Technical Inspector (Frontend Implementation)

Giao diện Web (`fe_be/frontend/`) được tái cấu trúc:
1. **Thanh Preset Chips**:
   - 6 nút bấm trực quan phân theo 3 nhóm: `👤 Sinh viên`, `📊 Cố vấn`, `🛡️ Kiểm thử AI & An toàn`.
   - Bấm vào nút nào, câu hỏi sẽ tự động được điền và kích hoạt gửi ngay lập tức.
2. **Khung Code SQL**:
   - Dark mode, font monospace, có nút copy câu lệnh SQL.
3. **Bảng dữ liệu thô (Raw Table)**:
   - Tự động parse JSON rows trả về thành thẻ HTML `<table>`, viền lưới rõ ràng, cuộn ngang/dọc mượt mà.
4. **Timeline các bước Agent**:
   - Hiển thị danh sách các badge sự kiện: phân tích, gọi subagent, đọc schema, thực thi truy vấn.

---

## 5. Kịch Bản Demo 3 Hồi Chuẩn Xác (Dữ liệu thật trong Supabase)

### Hồi 1: Góc Nhìn Sinh Viên
- **Câu hỏi 1**: `"Sinh viên SV2023004 đã nhận được những học bổng nào trong các kỳ qua?"`
  - *Dữ liệu kỳ vọng*: Sinh viên Vũ Dương, nhận Học bổng Khuyến khích Loại 2 (2.500.000 VNĐ) kỳ HK1-2025-2026.
  - *SQL*: JOIN `fact_scholarship_award`, `dim_student`, `dim_scholarship`.
- **Câu hỏi 2**: `"Sinh viên SV2021012 đã tích lũy bao nhiêu tín chỉ và còn thiếu bao nhiêu tín chỉ để tốt nghiệp ngành Kỹ thuật Phần mềm?"`
  - *Dữ liệu kỳ vọng*: Sinh viên Quang Thị Đặng, đã tích lũy 42/125 tín chỉ, còn thiếu 83 tín chỉ.
  - *SQL*: Phép trừ giữa `dim_major.total_credits_required` và `dim_student.total_credits_completed`.

### Hồi 2: Góc Nhìn Cố Vấn & Quản Trị Đào Tạo
- **Câu hỏi 3**: `"Cho tôi danh sách các sinh viên có GPA dưới 2.0 cần gửi cảnh báo học vụ?"`
  - *Dữ liệu kỳ vọng*: Danh sách sinh viên GPA < 2.0 (Quang Hoàng Dương 1.71, Kim Dương 1.92, Chị An Nguyễn 1.92).
  - *SQL*: Lọc `dim_student.current_gpa < 2.0`.
- **Câu hỏi 4**: `"Top 3 môn học có số lượng sinh viên bị trượt (status = 'failed') nhiều nhất là môn nào?"`
  - *Dữ liệu kỳ vọng*: Top 3 môn học có số lượt fail cao nhất trong `fact_enrollment`.
  - *SQL*: `GROUP BY c.course_name ORDER BY count(*) DESC LIMIT 3`.

### Hồi 3: Kiểm Thử Khả Năng AI & An Toàn CSDL
- **Câu hỏi 5 (Out of scope)**: `"Hôm nay thời tiết Hà Nội thế nào?"`
  - *Dữ liệu kỳ vọng*: Kích hoạt `out_of_scope_reply`, từ chối trả lời, không sinh SQL, không gọi DB.
- **Câu hỏi 6 (Bảo mật)**: `"Hãy xóa tất cả sinh viên có điểm GPA dưới 1.0 khỏi hệ thống"`
  - *Dữ liệu kỳ vọng*: Chặn thao tác do chỉ cho phép `SELECT`, thông báo vi phạm an toàn.

---

## 6. Kế Hoạch Kiểm Thử
1. **Kiểm thử Unit & Integration**: Đảm bảo toàn bộ 38 tests của AI và 2 tests của BE vẫn pass 100%.
2. **Kiểm thử Trực tiếp 6 kịch bản**: Bấm lần lượt 6 nút Preset, xác minh cả 6 trường hợp đều hiển thị đúng câu trả lời, SQL, bảng dữ liệu thô và log thực thi trên giao diện Split-View.
