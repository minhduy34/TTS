# Tài liệu Thiết kế: Sửa Lỗi Giao Diện & Tối Ưu Tốc Độ Phản Hồi Hệ Thống

**Ngày:** 2026-11-11  
**Dự án:** Hệ thống Multi-Agent NL-to-SQL hỗ trợ tra cứu học vụ (`c:\KHDL K46\TTS`)  
**Tác giả:** Trợ lý AI & Cái Minh Duy  

---

## 1. Bối cảnh & Vấn đề

1. **Lỗi hiển thị giao diện (Frontend):**
   - Ô nhập tin nhắn (`input-area`) bị đẩy khỏi đáy màn hình trên các thiết bị có viewport thấp hơn 820px (laptop có thanh Taskbar Windows, Bookmarks bar). Người dùng không nhìn thấy ô nhập liệu sau khi bot phản hồi.
   - Hộp tóm tắt (`content-block`) tự động mở ra một khung xám to bên dưới câu trả lời của trợ lý ngay cả khi chỉ chào hỏi đơn giản ("hi"), gây rối mắt và làm dài khung hội thoại.
2. **Độ trễ phản hồi tăng cao sau khi đổi DB Supabase (Backend):**
   - Supabase đặt tại máy chủ từ xa, mỗi lần kết nối TCP/TLS mất ~0.8s - 1.0s.
   - `get_schema()` và `execute_sql()` mở kết nối đơn lẻ `psycopg2.connect()` rồi đóng ngay cho từng tool call, gây lãng phí nhiều lần bắt tay mạng.
   - `get_schema()` query lại toàn bộ schema (bảng, cột, ràng buộc) trên mỗi câu hỏi yêu cầu SQL.
   - Sau khi có câu trả lời, hệ thống luôn chạy thêm 2 lệnh gọi LLM (`generate_summary` và `generate_content`) ngay cả với câu chào hỏi thông thường, gây chậm thêm 2-4 giây.

---

## 2. Mục tiêu Thiết kế

1. **Giao diện:**
   - Khung chat (`.app`) luôn co giãn responsive theo `height: calc(100vh - 24px)` hoặc `100dvh`, đảm bảo thanh gõ phím luôn hiển thị rõ ràng ở đáy màn hình.
   - Chuyển `content-block` thành nút bấm toggle: `📋 Xem tóm tắt nội dung` (mặc định ẩn), bấm vào mới bung ra.
   - Tự động cuộn mượt xuống cuối tin nhắn và focus vào ô nhập phím sau khi AI hoàn tất trả lời.
2. **Hiệu năng & Tốc độ:**
   - Sử dụng **Connection Pooling** (`ThreadedConnectionPool`) tái sử dụng kết nối PostgreSQL Supabase.
   - **In-Memory Schema Caching:** Cache kết quả `get_schema()` trong RAM server sau lần query đầu tiên.
   - **Giảm tải LLM:** Chỉ gọi `generate_content` khi có dữ liệu/SQL truy vấn; bỏ qua bước này với các câu chào hỏi xã giao thông thường.

---

## 3. Kiến trúc & Chi tiết Kỹ thuật

### 3.1. Frontend (`fe_be/frontend/style.css`, `app.js`, `index.html`)

- **CSS Layout (`style.css`):**
  ```css
  body {
    min-height: 100vh;
    height: 100vh;
    overflow: hidden;
  }
  .app {
    width: 100%;
    max-width: 780px;
    height: calc(100vh - 24px);
    margin: 12px auto;
    display: flex;
    flex-direction: column;
  }
  .chat-container {
    flex: 1;
    overflow-y: auto;
    min-height: 0;
  }
  .input-area {
    flex-shrink: 0;
  }
  ```

- **Toggle tóm tắt (`app.js`):**
  - Thêm toggle cho `content`:
    ```javascript
    if (content) {
      const toggle = document.createElement("div");
      toggle.className = "content-toggle";
      toggle.textContent = "📋 Xem tóm tắt nội dung";
      const box = document.createElement("div");
      box.className = "content-block";
      box.innerHTML = DOMPurify.sanitize(marked.parse(content));
      box.hidden = true;
      toggle.onclick = () => {
        box.hidden = !box.hidden;
        toggle.textContent = box.hidden ? "📋 Xem tóm tắt nội dung" : "🔼 Ẩn tóm tắt";
        chat.scrollTop = chat.scrollHeight;
      };
      contentWrap.appendChild(toggle);
      contentWrap.appendChild(box);
    }
    ```

### 3.2. Backend Database & Tool Optimization (`ai/src/agent/tools/sql_tools.py`)

- **Connection Pool:**
  ```python
  from psycopg2.pool import ThreadedConnectionPool
  from contextlib import contextmanager

  _pool = None

  def get_pool():
      global _pool
      if _pool is None:
          _pool = ThreadedConnectionPool(minconn=1, maxconn=5, dsn=os.getenv("DATABASE_URL"))
      return _pool

  @contextmanager
  def get_db_connection():
      pool = get_pool()
      conn = pool.getconn()
      try:
          yield conn
      finally:
          pool.putconn(conn)
  ```

- **In-Memory Schema Cache:**
  ```python
  _SCHEMA_CACHE = None

  @tool
  def get_schema() -> str:
      global _SCHEMA_CACHE
      if _SCHEMA_CACHE is not None:
          return _SCHEMA_CACHE
      # fetch from DB and store in _SCHEMA_CACHE
  ```

### 3.3. Tối ưu luồng gọi LLM (`ai/src/main.py`)

- Trong `main.py`, khi kết thúc luồng agent:
  - Nếu `not sql_query` và câu hỏi/trả lời ngắn (dưới 100 ký tự hoặc không có dữ liệu số liệu): bỏ qua `generate_content` hoặc gán rỗng `content = ""`.
  - Giảm bớt 1 lượt gọi API Gemini không cần thiết, giúp phản hồi các câu chào hỏi/trò chuyện thường nhanh tức thì (< 1.5s).

---

## 4. Kế hoạch Kiểm thử & Xác minh

1. **Kiểm thử Giao diện:**
   - Mở giao diện trên trình duyệt với các kích thước cửa sổ khác nhau (thu nhỏ, mở rộng, phóng to thanh tác vụ).
   - Xác nhận ô nhập phím luôn luôn hiển thị ở đáy màn hình.
   - Xác nhận nút `📋 Xem tóm tắt nội dung` ẩn/hiện mượt mà khi bấm.
2. **Kiểm thử Hiệu năng:**
   - Đo thời gian phản hồi câu chào "hi": trước ~4-6s -> sau kỳ vọng < 1.5s.
   - Đo thời gian phản hồi câu hỏi SQL "có bao nhiêu sinh viên": trước ~8-12s -> sau kỳ vọng giảm 40-50% nhờ connection pool và schema cache.
   - Kiểm tra log để xác nhận connection pool hoạt động ổn định và không bị rò rỉ kết nối.
