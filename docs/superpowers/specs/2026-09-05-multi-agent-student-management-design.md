# Multi-Agent Student Management System — Design Spec

**Date:** 2026-09-05  
**Domain:** Quản lý sinh viên (Student Management)  
**Status:** Approved

---

## 1. Overview

Hệ thống demo multi-agent AI cho phép sinh viên hỏi bằng ngôn ngữ tự nhiên về dữ liệu học tập (đăng ký học phần, điểm, tín chỉ, học bổng). Deep Agent đóng vai orchestrator — hiểu intent, quyết định gọi subagent hay tự trả lời. SQL Query Agent là subagent chuyên truy vấn database với ReAct reasoning loop.

---

## 2. Architecture Overview

```
User (Browser)
    │  SSE (EventSource)
    ▼
FastAPI (ai/src/main.py)
    │  serve static frontend + /chat/stream endpoint
    ▼
Deep Agent (LangGraph ReAct — Gemini Flash)
    ├── resolve_time_range(expression) → {start_date, end_date}
    ├── call_sql_agent(question, date_range?) → result + reasoning
    └── out_of_scope_reply()
              │
              ▼
      SQL Query Agent (LangGraph ReAct — Gemini Flash)
          ├── get_schema() → tables, columns, comments, FK relationships
          └── execute_sql(query) → rows

              │  asyncpg / psycopg2
              ▼
      Supabase PostgreSQL (cloud)
          Star Schema: fact_enrollment, fact_scholarship_award
          Dims: dim_student, dim_course, dim_semester, dim_major, dim_department, dim_scholarship
```

---

## 3. Database Design (Star Schema)

### 3.1 Fact Tables

#### `fact_enrollment`
Sự kiện sinh viên đăng ký một học phần trong một học kỳ.

| Column | Type | Description |
|---|---|---|
| enrollment_id | SERIAL PK | |
| student_id | INT FK → dim_student | |
| course_id | INT FK → dim_course | |
| semester_id | INT FK → dim_semester | |
| grade | NUMERIC(4,2) | Điểm số, thang 10. NULL nếu chưa có kết quả |
| grade_letter | VARCHAR(2) | A, B+, B, C+, C, D+, D, F |
| credits_earned | INT | Số tín chỉ đạt được (0 nếu trượt) |
| status | VARCHAR(20) | 'passed', 'failed', 'in_progress', 'withdrawn' |
| registered_at | TIMESTAMP | Thời điểm đăng ký |

#### `fact_scholarship_award`
Sự kiện sinh viên được trao học bổng một học kỳ.

| Column | Type | Description |
|---|---|---|
| award_id | SERIAL PK | |
| student_id | INT FK → dim_student | |
| scholarship_id | INT FK → dim_scholarship | |
| semester_id | INT FK → dim_semester | |
| amount_awarded | NUMERIC(12,2) | Số tiền thực tế được trao (VND) |
| awarded_at | DATE | Ngày trao học bổng |

### 3.2 Dimension Tables

#### `dim_student`
| Column | Type | Description |
|---|---|---|
| student_id | SERIAL PK | |
| student_code | VARCHAR(10) UNIQUE | Mã sinh viên, dạng SV2021001 |
| full_name | VARCHAR(100) | Họ và tên đầy đủ |
| gender | VARCHAR(10) | 'male', 'female', 'other' |
| date_of_birth | DATE | Ngày sinh |
| email | VARCHAR(100) | Email sinh viên (@student.edu.vn) |
| phone | VARCHAR(15) | Số điện thoại |
| major_id | INT FK → dim_major | Ngành học đang theo |
| admission_year | INT | Năm nhập học (2021, 2022, ...) |
| current_gpa | NUMERIC(3,2) | GPA tích lũy, thang 4.0 |
| total_credits_completed | INT | Tổng tín chỉ đã hoàn thành |
| status | VARCHAR(20) | 'active', 'graduated', 'suspended', 'dropped' |

#### `dim_course`
| Column | Type | Description |
|---|---|---|
| course_id | SERIAL PK | |
| course_code | VARCHAR(10) UNIQUE | Mã học phần, dạng CS101 |
| course_name | VARCHAR(200) | Tên học phần đầy đủ |
| credits | INT | Số tín chỉ của học phần (1-4) |
| department_id | INT FK → dim_department | Khoa phụ trách giảng dạy |
| description | TEXT | Mô tả nội dung học phần |
| is_required | BOOLEAN | Học phần bắt buộc hay tự chọn |
| prerequisites | VARCHAR(200) | Mã các học phần tiên quyết, phân cách bởi dấu phẩy |

#### `dim_semester`
| Column | Type | Description |
|---|---|---|
| semester_id | SERIAL PK | |
| semester_code | VARCHAR(20) UNIQUE | Mã học kỳ, dạng HK1-2024-2025 |
| semester_name | VARCHAR(50) | Tên hiển thị: Học kỳ 1 năm học 2024-2025 |
| academic_year | VARCHAR(10) | Năm học: 2024-2025 |
| semester_number | INT | 1, 2, hoặc 3 (học kỳ hè) |
| start_date | DATE | Ngày bắt đầu học kỳ |
| end_date | DATE | Ngày kết thúc học kỳ |
| is_current | BOOLEAN | TRUE nếu đây là học kỳ hiện tại |

#### `dim_major`
| Column | Type | Description |
|---|---|---|
| major_id | SERIAL PK | |
| major_code | VARCHAR(10) UNIQUE | Mã ngành, dạng CNTT |
| major_name | VARCHAR(100) | Tên ngành: Công nghệ Thông tin |
| faculty | VARCHAR(100) | Tên khoa chủ quản |
| total_credits_required | INT | Tổng tín chỉ cần hoàn thành để tốt nghiệp |
| duration_years | INT | Số năm đào tạo chuẩn (3, 4, 5) |

#### `dim_department`
| Column | Type | Description |
|---|---|---|
| department_id | SERIAL PK | |
| department_code | VARCHAR(10) UNIQUE | Mã khoa/bộ môn |
| department_name | VARCHAR(100) | Tên khoa/bộ môn |
| faculty | VARCHAR(100) | Tên khoa chủ quản (nếu là bộ môn) |
| head_name | VARCHAR(100) | Tên trưởng khoa/bộ môn |

#### `dim_scholarship`
| Column | Type | Description |
|---|---|---|
| scholarship_id | SERIAL PK | |
| scholarship_code | VARCHAR(20) UNIQUE | Mã học bổng |
| scholarship_name | VARCHAR(200) | Tên học bổng đầy đủ |
| scholarship_type | VARCHAR(50) | 'merit' (học lực), 'need' (hoàn cảnh), 'enterprise' (doanh nghiệp) |
| amount | NUMERIC(12,2) | Giá trị học bổng mỗi kỳ (VND) |
| min_gpa | NUMERIC(3,2) | GPA tối thiểu để đủ điều kiện xét |
| description | TEXT | Mô tả điều kiện và ý nghĩa học bổng |

### 3.3 PostgreSQL COMMENTs
Mỗi table và column đều có `COMMENT ON TABLE/COLUMN` để SQL Agent đọc qua `get_schema()` tool mà không cần hardcode domain knowledge.

---

## 4. Agent Architecture

### 4.1 Deep Agent (Orchestrator)

**Framework:** LangGraph ReAct agent  
**LLM:** Gemini Flash (`gemini-flash-latest`)  
**Conversation memory:** In-memory dict keyed by `session_id`, lưu `List[BaseMessage]`

**System prompt personality:**
- Xưng "mình", gọi user là "bạn"
- Dùng emoji tự nhiên (🎓📚😅🥲✨)
- Ngắn gọn, thân thiện, phong cách Gen Z / sinh viên
- Biết phạm vi: chỉ trả lời về học tập, học phần, điểm, tín chỉ, học bổng
- Out-of-scope: từ chối lịch sự, gợi ý câu hỏi phù hợp

**Tools:**

| Tool | Input | Output | Mô tả |
|---|---|---|---|
| `resolve_time_range` | `expression: str` | `{start_date, end_date, label}` | Convert "tháng trước", "quý 2", "năm ngoái", "học kỳ này" → date range tuyệt đối. Dùng ngày hiện tại + tra dim_semester cho các expression học kỳ |
| `call_sql_agent` | `question: str, date_range: dict?` | `{result, reasoning, sql_query}` | Gọi SQL Query Agent, truyền câu hỏi và date range nếu có |
| `out_of_scope_reply` | `topic: str` | `str` | Trả về câu từ chối vui vẻ kèm gợi ý |

**Decision logic:**
```
intent == greeting / simple question → tự trả lời
intent có time expression → resolve_time_range() trước → call_sql_agent()
intent cần dữ liệu DB → call_sql_agent() trực tiếp
intent ngoài domain → out_of_scope_reply()
```

### 4.2 SQL Query Agent (Subagent)

**Framework:** LangGraph ReAct agent (độc lập, được deep agent gọi như function)  
**LLM:** Gemini Flash  
**Max iterations:** 5 (tránh loop vô hạn)

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `get_schema` | none | Full schema: tên bảng, cột, type, COMMENT, FK relationships, sample values |
| `execute_sql` | `query: str` | `{rows: List[dict], row_count: int, error: str?}` |

**ReAct reasoning loop:**
1. **Observe** — gọi `get_schema()`, đọc descriptions
2. **Think** — reasoning bắt buộc phải explicit: bảng nào cần, cột nào select, join điều kiện gì, WHERE filter gì, tại sao
3. **Act** — generate SQL (chỉ SELECT, không INSERT/UPDATE/DELETE)
4. **Observe** — chạy `execute_sql()`, xem kết quả hoặc lỗi
5. **Reflect** — nếu lỗi hoặc empty result → phân tích lý do, điều chỉnh query
6. **Return** — `{result, reasoning, sql_query}` về Deep Agent

**Safety:** SQL Agent chỉ được phép chạy SELECT queries. Nếu detect non-SELECT → từ chối, báo Deep Agent.

---

## 5. FastAPI + Streaming

### 5.1 Endpoints

| Method | Path | Description |
|---|---|---|
| `GET /` | — | Serve `frontend/index.html` |
| `GET /chat/stream` | `?session_id=&message=` | SSE stream — main chat endpoint |
| `GET /health` | — | `{"status": "ok"}` |

### 5.2 SSE Event Types

```
event: status   → {"message": "🧠 Deep Agent đang phân tích câu hỏi..."}
event: status   → {"message": "🔧 Gọi tool: resolve_time_range"}
event: status   → {"message": "📅 Khoảng thời gian: 01/08 → 31/08/2026"}
event: status   → {"message": "📊 Đang hỏi SQL Agent..."}
event: status   → {"message": "📋 SQL Agent đang đọc schema..."}
event: status   → {"message": "✍️ SQL Agent đang tạo câu query..."}
event: status   → {"message": "⚡ Đang thực thi SQL..."}
event: done     → {"reply": "...", "reasoning": "...", "sql_query": "..."}
event: error    → {"message": "..."}
```

LangGraph `.astream_events()` emit các `on_tool_start` / `on_tool_end` / `on_chain_start` events → FastAPI map sang SSE events trên.

### 5.3 Frontend Structure

```
frontend/
  index.html   ← Layout: sidebar trống (có thể mở rộng) + chat area
  style.css    ← Gradient tím-xanh, bubble chat, font tròn
  app.js       ← EventSource logic, render bubbles, collapsible reasoning
```

**UI components:**
- **Status bar** — hiện ngay dưới bubble user, cập nhật real-time theo SSE `status` events
- **Chat bubble user** — icon 🎓, align right
- **Chat bubble agent** — icon 🤖, align left, hỗ trợ markdown render cơ bản
- **Reasoning panel** — collapsible "Xem cách mình nghĩ 🔍" — hiện SQL query + reasoning text của SQL Agent
- **Input area** — textarea + Enter để gửi

---

## 6. Project Structure

```
TTS/
├── ai/
│   ├── src/
│   │   ├── main.py
│   │   ├── agent/
│   │   │   ├── deep_agent.py
│   │   │   ├── llm.py
│   │   │   ├── history.py
│   │   │   ├── tool_registry.py
│   │   │   ├── subagent_registry.py
│   │   │   ├── prompt/
│   │   │   │   └── deep_agent.py
│   │   │   ├── tools/
│   │   │   │   ├── datetime_tools.py
│   │   │   │   └── sql_tools.py
│   │   │   └── subagents/
│   │   │       └── sql_query_agent.py
│   │   └── frontend/
│   │       ├── index.html
│   │       ├── style.css
│   │       └── app.js
│   ├── requirements.txt
│   └── .env
├── be/
│   ├── schema.sql
│   ├── seed.py
│   └── .env
└── docs/
    └── superpowers/specs/
        └── 2026-09-05-multi-agent-student-management-design.md
```

---

## 7. Tech Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini Flash (`gemini-flash-latest`) |
| Agent Framework | LangChain + LangGraph |
| Backend | FastAPI + uvicorn |
| Database | Supabase PostgreSQL (cloud, free tier) |
| DB Driver | psycopg2-binary (sync cho schema tool), asyncpg (async queries) |
| Streaming | Server-Sent Events (SSE) via `StreamingResponse` |
| Frontend | HTML5 / CSS3 / Vanilla JS |
| Dummy Data | Faker (Python), ~100 sinh viên |
| Env management | python-dotenv |

---

## 8. Dummy Data Scope

Seed script (`be/seed.py`) tạo:
- **5 majors** (CNTT, KTPM, HTTT, MMT, KHMT)
- **4 departments** (Khoa CNTT, Toán, Ngoại ngữ, Đại cương)
- **6 semesters** (HK1/HK2 từ 2023-2024 đến 2025-2026, HK1 2026-2027 là current)
- **30 courses** (mix bắt buộc + tự chọn, 2-4 tín chỉ)
- **100 students** (random GPA, ngành, năm nhập học 2021-2024)
- **~400 enrollments** (mỗi sinh viên 3-5 môn/kỳ, nhiều kỳ)
- **4 scholarships** (học lực, hoàn cảnh, doanh nghiệp)
- **~60 scholarship awards** (sinh viên GPA cao hoặc khó khăn)
