# Sửa Lỗi Giao Diện & Tối Ưu Tốc Độ Phản Hồi Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Khắc phục triệt để lỗi giao diện bị trôi khuất thanh nhập liệu và hộp tóm tắt bung rộng, đồng thời tối ưu hóa tốc độ kết nối cơ sở dữ liệu Supabase và giảm thiểu các lệnh gọi LLM dư thừa.

**Architecture:** 
- Frontend: Cập nhật CSS bố cục responsive (viewport dynamic height) để giữ ô input luôn ở đáy màn hình; chuyển hộp tóm tắt `content-block` thành component nút bấm toggle mở rộng/thu gọn.
- Backend: Triển khai connection pool (`ThreadedConnectionPool`) và in-memory caching cho `get_schema()` trong `sql_tools.py`; điều kiện hóa việc gọi `generate_content` trong `main.py` để tránh gọi Gemini thừa đối với các câu chào hỏi/trò chuyện thường.

**Tech Stack:** FastAPI, LangGraph, LangChain, psycopg2-binary, HTML5/CSS3, Vanilla JavaScript, DOMPurify, Marked.

---

### Task 1: Cập nhật Layout CSS và Tự Động Focus Ô Chat

**Files:**
- Modify: `fe_be/frontend/style.css:1-40`
- Modify: `fe_be/frontend/index.html:1-41`

**Step 1: Cập nhật style.css**
- Đặt `body` với `height: 100vh; overflow: hidden;`
- Đặt `.app` với `height: calc(100vh - 20px); max-height: calc(100vh - 20px); margin: 10px auto;`
- Đảm bảo `.chat-container` có `flex: 1; overflow-y: auto; min-height: 0;`
- Đảm bảo `.input-area` có `flex-shrink: 0;`

**Step 2: Thêm style cho nút toggle tóm tắt `.content-toggle`**
```css
.content-toggle {
  font-size: 0.78rem;
  color: #667eea;
  cursor: pointer;
  margin-top: 6px;
  user-select: none;
}
.content-toggle:hover { text-decoration: underline; }
```

**Step 3: Cập nhật cache-busting trong index.html**
- Đổi version `style.css?v=fresh4` và `app.js?v=fresh4`

**Step 4: Kiểm tra và xác minh**
- Kiểm tra tính hợp lệ của file CSS và HTML.

**Step 5: Commit**
```bash
git add fe_be/frontend/style.css fe_be/frontend/index.html
git commit -m "fix(fe): fix app viewport height overflow and add content-toggle style"
```

---

### Task 2: Chuyển Hộp Tóm Tắt Thành Nút Bấm Toggle Thu Gọn/Mở Rộng

**Files:**
- Modify: `fe_be/frontend/app.js:79-88`

**Step 1: Viết logic toggle cho `content` trong app.js**
Thay thế đoạn append trực tiếp `.content-block` bằng toggle:
```javascript
  if (content && content.trim()) {
    const contentToggle = document.createElement("div");
    contentToggle.className = "content-toggle";
    contentToggle.textContent = "📋 Xem tóm tắt nội dung";
    const contentBlock = document.createElement("div");
    contentBlock.className = "content-block";
    contentBlock.innerHTML = DOMPurify.sanitize(marked.parse(content));
    contentBlock.hidden = true;
    contentToggle.onclick = () => {
      contentBlock.hidden = !contentBlock.hidden;
      contentToggle.textContent = contentBlock.hidden ? "📋 Xem tóm tắt nội dung" : "🔼 Ẩn tóm tắt";
      chat.scrollTop = chat.scrollHeight;
    };
    contentWrap.appendChild(contentToggle);
    contentWrap.appendChild(contentBlock);
  }
```

**Step 2: Kiểm tra chức năng toggle**
- Xác nhận logic ẩn/hiện và cuộn mượt hoạt động chuẩn xác.

**Step 3: Commit**
```bash
git add fe_be/frontend/app.js
git commit -m "feat(fe): make response content block collapsible toggle"
```

---

### Task 3: Triển Khai Connection Pool & In-Memory Schema Caching Cho Database

**Files:**
- Modify: `ai/src/agent/tools/sql_tools.py`

**Step 1: Thêm `ThreadedConnectionPool` và hàm quản lý kết nối contextmanager**
- Khởi tạo pool với 1 đến 5 kết nối sẵn sàng.
- Sử dụng `@contextmanager` để `getconn()` và `putconn()`.

**Step 2: Triển khai Cache cho `get_schema()`**
- Sử dụng biến `_SCHEMA_CACHE: str | None = None`.
- Lần đầu gọi sẽ truy vấn DB và gán vào cache; các lần sau trả về ngay lập tức không tốn kết nối mạng.

**Step 3: Kiểm tra tốc độ đọc schema**
- Chạy script đo thời gian `get_schema()` trước và sau khi có cache.

**Step 4: Commit**
```bash
git add ai/src/agent/tools/sql_tools.py
git commit -m "perf(ai): add database connection pooling and schema in-memory caching"
```

---

### Task 4: Giảm Thiểu Các Lượt Gọi LLM Không Cần Thiết Trong Main

**Files:**
- Modify: `ai/src/agent/content.py`
- Modify: `ai/src/main.py`

**Step 1: Cập nhật `generate_content`**
- Nếu không có `sql_query` hoặc `reply` ngắn (dưới 80 ký tự chào hỏi), trả về chuỗi rỗng `""` ngay lập tức mà không gọi Gemini API.

**Step 2: Đo lường và kiểm thử End-to-End**
- Test gửi câu hỏi "hi" -> kiểm tra thời gian phản hồi.
- Test gửi câu hỏi SQL "có bao nhiêu sinh viên" -> kiểm tra kết quả truy vấn và hiển thị trên giao diện.

**Step 3: Commit**
```bash
git add ai/src/agent/content.py ai/src/main.py
git commit -m "perf(ai): prune redundant LLM calls on conversational turns"
```
