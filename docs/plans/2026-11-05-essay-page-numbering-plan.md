# Kế hoạch Triển khai Đánh số trang cho Bài tiểu luận Học thuật Word

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Triển khai đánh số trang tự động vào chân trang (Footer Center) cho bài tiểu luận Word, bắt đầu số 1 từ Mục lục, không đánh số trang bìa.

**Architecture:** Sử dụng `python-docx` và `parse_xml` để cấu hình OpenXML cho Section Footer, ngắt liên kết giữa trang bìa và thân bài, chèn trường động `w:fldSimple w:instr="PAGE"` và đồng bộ Mục lục.

**Tech Stack:** Python 3.11, python-docx, OpenXML (WordprocessingML).

---

### Task 1: Cập nhật mã nguồn `ai/src/generate_essay.py` với cấu hình Page Numbering

**Files:**
- Modify: `ai/src/generate_essay.py`

**Step 1: Viết hàm bổ trợ chèn trường số trang `add_page_number` và cấu hình Footer Section 2**

Trong `ai/src/generate_essay.py`:
1. Viết hàm `add_page_number_to_section(section)`:
   - Ngắt thừa kế footer: `section.footer.is_linked_to_previous = False`
   - Đặt số trang bắt đầu: `w:pgNumType w:start="1"`
   - Lấy `p = section.footer.paragraphs[0]`, căn giữa `WD_ALIGN_PARAGRAPH.CENTER`
   - Tạo run và chèn trường `w:fldSimple w:instr="PAGE"` với font Times New Roman 11pt.
2. Đảm bảo `sect_cover` (Section 1) có footer rỗng và `is_linked_to_previous = False`.
3. Cập nhật bảng `toc_data` với các số trang chuẩn xác:
   - Mục lục: 1
   - Danh mục thuật ngữ & Tóm tắt: 2
   - Chương 1: 3
   - Chương 2: 5
   - Chương 3: 8
   - Chương 4: 13
   - Chương 5: 17
   - Tài liệu tham khảo: 19

**Step 2: Chạy kiểm tra cú pháp Python**
Command:
```powershell
uv run python -m py_compile ai/src/generate_essay.py
```
Expected: Exit code 0, không có lỗi cú pháp.

---

### Task 2: Sinh tài liệu `.docx` và kiểm thử xác thực cấu trúc trang

**Files:**
- Target: `Tieu_Luan_Multi_Agent_NL_to_SQL_KHDL.docx`

**Step 1: Thực thi script sinh file Word**
Command:
```powershell
uv run python ai/src/generate_essay.py
```
Expected: "Tạo tài liệu Word thành công: ...Tieu_Luan_Multi_Agent_NL_to_SQL_KHDL.docx"

**Step 2: Viết script kiểm tra xác thực cấu trúc trang (Automated Verification)**
Kiểm tra bằng script:
1. `doc.sections[0].footer.paragraphs[0].text` trống rỗng.
2. `doc.sections[1].footer.paragraphs[0]` chứa trường `w:instr="PAGE"`.
3. Thuộc tính `_sectPr` của Section 2 chứa `w:pgNumType` với `w:start="1"`.

**Step 3: Cập nhật task tracker và commit**
Cập nhật `docs/plans/task.md` đánh dấu hoàn thành và commit code.

