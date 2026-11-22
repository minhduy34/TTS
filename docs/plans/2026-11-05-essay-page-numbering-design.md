# Thiết kế Kỹ thuật Đánh số trang cho Bài tiểu luận Học thuật Word (.docx)

- **Ngày lập:** 2026-11-05
- **Tác giả:** Trợ lý AI Sinh Viên (Pair Programming)
- **Dự án:** TTS - Hệ thống Multi-Agent NL-to-SQL
- **Tài liệu mục tiêu:** `Tieu_Luan_Multi_Agent_NL_to_SQL_KHDL.docx` (sinh bởi `ai/src/generate_essay.py`)

---

## 1. Mục tiêu và Yêu cầu
- **Yêu cầu cốt lõi:** Đánh số trang cho toàn bộ nội dung bài tiểu luận, **ngoại trừ trang bìa**.
- **Quy tắc bắt đầu:** Trang Mục lục (bắt đầu Section 2) được tính là **trang 1**.
- **Vị trí và Kiểu dáng:** Chân trang ở giữa (Footer Center), font **Times New Roman**, cỡ **11pt**, tuân thủ nghiêm ngặt quy cách trình bày học thuật của Trường Đại học Quy Nhơn.
- **Tính năng tự động:** Sử dụng trường OpenXML động (`w:fldSimple w:instr="PAGE"`), đảm bảo tương thích 100% với Microsoft Word, WPS Office, LibreOffice và Google Docs.

---

## 2. Kiến trúc & Giải pháp Kỹ thuật

### 2.1. Phân tách Section trong python-docx
Tài liệu được chia làm 2 Section:
1. **Section 1 (`doc.sections[0]`): Trang bìa chính thức**
   - Viền đôi nghệ thuật (`w:pgBorders`).
   - Ngắt kết nối footer và xóa nội dung footer:
     ```python
     sect_cover = doc.sections[0]
     # Đảm bảo footer trang bìa hoàn toàn rỗng
     sect_cover.footer.is_linked_to_previous = False
     for p in sect_cover.footer.paragraphs:
         p.text = ""
     ```

2. **Section 2 (`sect_body`): Toàn bộ phần nội dung (từ Mục lục đến hết)**
   - Hủy bỏ viền trang (`w:val="none"`).
   - Ngắt kế thừa footer từ trang bìa:
     ```python
     sect_body.footer.is_linked_to_previous = False
     ```
   - Thiết lập số trang khởi đầu là `1`:
     ```python
     pgNumType = parse_xml(f'<w:pgNumType {nsdecls("w")} w:start="1"/>')
     sect_body._sectPr.append(pgNumType)
     ```
   - Chèn trường số trang động vào đoạn văn bản ở footer:
     ```python
     footer_p = sect_body.footer.paragraphs[0]
     footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
     # Chèn w:fldSimple w:instr="PAGE" với font Times New Roman 11pt
     ```

### 2.2. Đồng bộ hóa Mục lục (TOC Mapping)
Cập nhật mảng chỉ số trang trong Mục lục để phản ánh đúng cấu trúc trang thực tế sau ngắt trang:
- **Mục lục:** Trang 1
- **Danh mục thuật ngữ & Tóm tắt đề tài:** Trang 2
- **Chương 1: Giới thiệu đề tài và Bài toán thực tiễn:** Trang 3
- **Chương 2: Cơ sở lý thuyết và Công nghệ nền tảng:** Trang 5
- **Chương 3: Phân tích và Thiết kế hệ thống:** Trang 8
- **Chương 4: Triển khai thực nghiệm và Đánh giá kết quả:** Trang 13
- **Chương 5: Kết luận và Hướng phát triển:** Trang 17
- **Tài liệu tham khảo:** Trang 19

---

## 3. Kế hoạch kiểm thử (Verification Plan)
1. Chạy script `ai/src/generate_essay.py` để biên dịch lại file `.docx`.
2. Kiểm tra tài liệu sinh ra bằng python script kiểm tra cấu trúc OpenXML:
   - Xác nhận Section 1 không có footer hoặc footer rỗng.
   - Xác nhận Section 2 có `w:pgNumType w:start="1"` và trường `PAGE`.
   - Xác nhận kích thước file `.docx` hợp lệ (> 80KB) và không bị lỗi XML corruption.
3. Cập nhật `docs/plans/task.md`.

