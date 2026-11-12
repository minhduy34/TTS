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
