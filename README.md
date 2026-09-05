# TTS — Student AI Assistant

Hệ thống trợ lý AI quản lý sinh viên, gồm hai service chạy song song:

| Service | Thư mục | Port | Mô tả |
|---------|---------|------|--------|
| AI Service | `ai/` | 8001 | Multi-agent LangGraph + Gemini, kết nối DB |
| Backend / Frontend | `fe_be/` | 8000 | FastAPI proxy + giao diện web |

---

## Yêu cầu

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (package manager)
- Tài khoản [Supabase](https://supabase.com) (PostgreSQL)
- Gemini API Key từ [Google AI Studio](https://aistudio.google.com/apikey)

---

## 1. Clone repo

```bash
git clone https://github.com/nhando12/TTS.git
cd TTS
git checkout dev
```

---

## 2. Cài đặt Database (Supabase)

1. Tạo project mới trên Supabase, lấy **Connection String** dạng:
   ```
   postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
   ```

2. Vào **SQL Editor** trên Supabase, chạy toàn bộ nội dung file [fe_be/schema.sql](fe_be/schema.sql) để tạo bảng.

3. Tạo file `fe_be/.env` từ mẫu:
   ```bash
   cp fe_be/.env.example fe_be/.env
   ```
   Điền `DATABASE_URL` vào `fe_be/.env`:
   ```env
   DATABASE_URL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
   ```

4. Seed dữ liệu mẫu:
   ```bash
   cd fe_be
   uv run python seed.py
   cd ..
   ```

---

## 3. Cấu hình AI Service

1. Tạo file `ai/.env` từ mẫu:
   ```bash
   cp ai/.env.example ai/.env
   ```

2. Điền vào `ai/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
   ```
   > Dùng cùng `DATABASE_URL` với bước 2.

---

## 4. Cài đặt dependencies

```bash
# AI Service
cd ai
uv sync
cd ..

# Backend / Frontend
cd fe_be
uv sync
cd ..
```

---

## 5. Chạy — mở 2 terminal

### Terminal 1 — AI Service (port 8001)

```bash
cd ai/src
uv run python main.py
```

### Terminal 2 — Backend + Frontend (port 8000)

```bash
cd fe_be
uv run python main.py
```

Sau khi cả hai service đã chạy, mở trình duyệt tại:

```
http://localhost:8000
```

---

## Cấu trúc dự án

```
TTS/
├── ai/                        # AI Service (port 8001)
│   ├── src/
│   │   ├── agent/             # LangGraph agents, tools, prompts
│   │   ├── utils/
│   │   └── main.py            # FastAPI entrypoint
│   ├── .env.example
│   └── pyproject.toml
│
├── fe_be/                     # Backend proxy + Frontend (port 8000)
│   ├── frontend/              # HTML/CSS/JS giao diện web
│   ├── main.py                # FastAPI entrypoint
│   ├── schema.sql             # Schema PostgreSQL
│   ├── seed.py                # Script tạo dữ liệu mẫu
│   ├── .env.example
│   └── pyproject.toml
│
└── pipeline.drawio            # Sơ đồ kiến trúc hệ thống
```

---

## Biến môi trường

| File | Biến | Mô tả |
|------|------|--------|
| `ai/.env` | `GEMINI_API_KEY` | API key Gemini (Google AI Studio) |
| `ai/.env` | `DATABASE_URL` | PostgreSQL connection string (Supabase) |
| `fe_be/.env` | `DATABASE_URL` | PostgreSQL connection string (Supabase) |
