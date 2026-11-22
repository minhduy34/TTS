| Task | Status | Details |
| --- | --- | --- |
| Thiết kế hệ thống Demo Kỹ thuật Split-View | Completed | Đã hoàn thành và lưu tài liệu thiết kế tại `docs/plans/2026-09-09-technical-inspector-demo-design.md` |
| Lập kế hoạch thực thi chi tiết | Completed | Đã lưu tại `docs/plans/2026-09-09-technical-inspector-demo-plan.md` |
| Task 1-6: Phát triển và kiểm thử Demo Split-View | Completed | Đã hoàn thành toàn bộ tính năng và test pass |
| Thiết kế và sinh tài liệu bài tiểu luận học thuật (Word) | Completed | Đã sinh file `Tieu_Luan_Multi_Agent_NL_to_SQL_KHDL.docx` chuẩn phong cách học thuật QNU |
| Khôi phục mã nguồn ban đầu | Completed | Đã khôi phục toàn bộ code về bản gốc ban đầu theo yêu cầu người dùng |
| Thiết kế kỹ thuật đánh số trang tiểu luận Word | Completed | Đã lưu tài liệu thiết kế tại `docs/plans/2026-11-05-essay-page-numbering-design.md` |
| Cấu hình DB Supabase mới & nạp dữ liệu học vụ | Completed | Đã nạp thành công 2.769 bản ghi vào DB mới của người dùng và test truy vấn đạt 100% |
| Sửa lỗi giao diện bị khoá không nhập được câu hỏi tiếp theo | Completed | Khôi phục đúng layout CSS `.app`, sửa cuộn tin nhắn, thêm định dạng bảng và tự động focus ô nhập liệu |
| Thiết kế sửa lỗi tràn giao diện & tăng tốc độ phản hồi | Completed | Đã lưu tại `docs/plans/2026-11-11-ui-layout-and-performance-optimization-design.md` |
| Lập kế hoạch thực thi chi tiết (4 Tasks) | Completed | Đã lưu tại `docs/plans/2026-11-11-ui-layout-and-performance-optimization-plan.md` |
| Task 1: Cập nhật Layout CSS & Viewport Bounds | Completed | Khắc phục triệt để tràn viền màn hình, cố định ô nhập luôn ở đáy màn hình (`c5b97a8`) |
| Task 2: Chuyển Hộp Tóm Tắt Thành Toggle Thu Gọn/Mở Rộng | Completed | Thêm nút bấm `📋 Xem tóm tắt nội dung` (mặc định ẩn, bấm vào mới bung ra) (`c389a78`) |
| Task 3: Triển Khai Connection Pool & Schema Cache | Completed | Dùng `ThreadedConnectionPool` và cache RAM cho `get_schema()` (giảm từ 1.2s xuống 0.0008s) (`aada60f`) |
| Task 4: Giảm Thiểu Các Lượt Gọi LLM Dư Thừa | Completed | Bỏ gọi LLM tóm tắt thừa khi trò chuyện thường/không dùng SQL (`7b13e46`, `b198dad`) |
| Brainstorming 1: Khám phá ngữ cảnh dự án, bài báo và bìa.docx | Completed | Đã đọc toàn bộ codebase (`ai/`, `fe_be/`), `bìa.docx`, và 2 bài báo PDF (`2312.11242v6.pdf` - MAC-SQL, `2507.14372v1.pdf` - LinkedIn Text-to-SQL) |
| Brainstorming 2: Hỏi câu hỏi làm rõ yêu cầu (từng câu một) | Completed | Đã chốt: (1) Bìa theo `bìa.docx` với Sinh viên: Cái Minh Duy - MSSV: 4654110003, HP: Xử lý Ngôn ngữ Tự nhiên (NLP), GVHD: TS. Lê Quang Hùng, tên đề tài mới; (2) Nội dung bám sát 100% source code thực tế (PostgreSQL/Supabase 8 bảng Star Schema + LangGraph + Gemini) kết hợp lý thuyết MAC-SQL & LinkedIn Text-to-SQL; (3) Hình ảnh kết hợp logo `bìa.docx` + hình 2 bài báo PDF + sơ đồ/biểu đồ TikZ/pgfplots + ảnh giao diện |
| Brainstorming 3: Đề xuất 2-3 phương án thiết kế tiểu luận LaTeX | Completed | Người dùng đã chọn Phương án 1: Cấu trúc nguyên khối `report/main.tex` + `report/references.bib` + `report/figures/` |
| Brainstorming 4: Trình bày thiết kế chi tiết theo từng phần và lấy xác nhận | Completed | Người dùng đã duyệt toàn bộ 3 phần thiết kế |
| Brainstorming 5: Lưu tài liệu thiết kế vào `docs/plans/2026-11-22-latex-essay-text-to-sql-design.md` | Completed | Đã tạo và lưu tài liệu thiết kế chi tiết |
| Brainstorming 6: Chuyển sang kỹ năng `writing-plans` để lập kế hoạch thực thi | Completed | Đã lưu kế hoạch chi tiết tại `docs/plans/2026-11-22-latex-essay-text-to-sql-plan.md` |
| Task 1 (LaTeX Plan): Trích xuất và chuẩn bị tài nguyên hình ảnh trong `report/figures/` | Completed | Đã trích xuất `report/figures/logo_qnu.png` (258.8 KB) từ `bìa.docx` và kiểm thử PASS |
| Task 2 (LaTeX Plan): Xây dựng cơ sở dữ liệu tài liệu tham khảo `report/references.bib` | Completed | Đã tạo `report/references.bib` với 12 trích dẫn chuẩn và kiểm thử PASS |
| Task 3 (LaTeX Plan): Xây dựng Preamble, Trang bìa, Tóm tắt, Chương 1 & Chương 2 trong `report/main.tex` | Completed | Đã hoàn thành phần mở đầu, bìa chuẩn `bìa.docx`, Tóm tắt, Chương 1 & Chương 2 và kiểm thử PASS |
| Task 4 (LaTeX Plan): Xây dựng Chương 3, Chương 4, Chương 5 & Kiểm định cú pháp LaTeX toàn cục | Completed | Đã hoàn thiện `report/main.tex` (1.339 dòng, 84 cặp môi trường cân bằng, 12 trích dẫn BibTeX, 8 hình/biểu đồ, 7 bảng biểu, 9 công thức đánh số) và kiểm thử PASS |
| Biên dịch và tinh chỉnh bản PDF cuối cùng từ LaTeX | Completed | Đã biên dịch thành công bằng TeX Live (`pdflatex` + `bibtex`) ra `report/main.pdf` và `report/Tieu_Luan_Text_to_SQL_Cai_Minh_Duy_4654110003.pdf` (47 trang, 779 KB) |
| Đọc DB trực tiếp & thống kê dữ liệu thực tế | Completed | Đã khởi tạo & đọc DB 8 bảng Star Schema (`fe_be/student.db` đồng bộ 100% từ `schema.sql` & `seed.py`): tổng 2.958 bản ghi (`fact_enrollment`: 2.769, `fact_scholarship_award`: 39, `dim_student`: 100, `dim_course`: 30, `dim_semester`: 7, `dim_major`: 5, `dim_department`: 4, `dim_scholarship`: 4) |
| Tự tạo Benchmark, tự chạy & tự đánh giá theo công thức (EX, EM, CSR, Latency) | Completed | Đã tạo `ai/src/benchmark_data.json` (20 câu hỏi 4 mức độ khó) & `ai/src/run_benchmark.py`, chạy thực nghiệm thật ra `report/benchmark_results.json` (Baseline: EX 45.0%/EM 40.0%/CSR 90.0%; +Selector: EX 90.0%/EM 85.0%/CSR 95.0%; Full Pipeline: EX 95.0%/EM 85.0%/CSR 100.0%) |
| Tự chạy các file `main.py` (`ai/src/main.py` & `fe_be/main.py`) để test E2E | Completed | Đã khởi chạy cả `ai/src/main.py` (8001) và `fe_be/main.py` (8000), kiểm thử E2E `/health`, `/` và 3 kịch bản `/chat/stream` SSE streaming đạt 100% PASS (lưu tại `report/e2e_test_results.json`) |
| Đồng bộ số liệu thực nghiệm thật vào `report/main.tex` & biên dịch lại PDF | Completed | Đã đồng bộ 100% số liệu DB (2.958 bản ghi), kết quả benchmark tự động (`report/benchmark_results.json`) và E2E (`report/e2e_test_results.json`) vào `report/main.tex` và xuất lại `report/main.pdf` & `report/Tieu_Luan_Text_to_SQL_Cai_Minh_Duy_4654110003.pdf` (788.6 KB) |
