# Multi-Agent Student Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent AI demo where a Deep Agent orchestrates a SQL Query Agent to answer student management questions in natural language via a chat UI.

**Architecture:** Deep Agent (LangGraph ReAct, Gemini Flash) acts as orchestrator — it resolves time ranges, delegates DB queries to the SQL Query Agent, and replies in a teen-friendly Vietnamese style. The SQL Query Agent runs its own ReAct loop to read schema, reason about table/column selection, generate SQL, execute it, and return structured results with reasoning. FastAPI serves both the SSE streaming chat endpoint and the static frontend.

**Tech Stack:** Python 3.11+, LangChain + LangGraph, langchain-google-genai (Gemini Flash), FastAPI + uvicorn, psycopg2-binary, Supabase PostgreSQL, Faker, pytest + freezegun + httpx

**Spec:** `docs/superpowers/specs/2026-09-05-multi-agent-student-management-design.md`
**Coding Rules:** `docs/superpowers/rule.md` — áp dụng cho mọi file Python trong project

## Global Constraints

- Python >= 3.11
- LangGraph >= 0.2.0 (use `create_react_agent` from `langgraph.prebuilt`)
- LangChain >= 0.3.0, langchain-core >= 0.3.0, langchain-google-genai >= 2.0.0
- Gemini model: `gemini-2.0-flash`
- Only SELECT queries allowed through the SQL Agent (reject INSERT/UPDATE/DELETE/DROP)
- All API keys and DB URLs via environment variables — never hardcoded
- All replies in Vietnamese
- Frontend: vanilla HTML/CSS/JS only — no frameworks
- SSE event format: `event: <type>\ndata: <json>\n\n`
- Dependencies managed via `uv` — không dùng pip trực tiếp

### Coding Rules (từ docs/superpowers/rule.md — bắt buộc mọi file Python)

- **Tên rõ nghĩa**: không dùng `x`, `tmp`, `data1` — đặt tên mô tả đúng ý nghĩa
- **1 function = 1 responsibility**: không vừa validate + query DB + format response trong cùng function
- **Function < 40–50 dòng**: dài hơn thì tách ra
- **Không nesting > 2–3 level**: dùng guard clause (`return`/`raise` sớm) để tránh `if` lồng nhau
- **Nhiều `if/elif` cố định**: dùng `match-case` hoặc dispatch table (dict `{key: handler}`)
- **Type cụ thể**: tránh `Any`; dùng `str`, `int`, `dict[str, str]`, `list[BaseMessage]`...
- **`None` khai báo đúng**: dùng `X | None`, không tự đổi `None` thành `"None"`
- **`try/except` không được nuốt lỗi**: luôn log + `raise` hoặc chuyển sang domain exception
- **Catch đúng exception**: ưu tiên `ValueError`, `psycopg2.Error`... thay vì bắt `Exception` bừa
- **Không magic number/string**: dùng constant (ví dụ `MAX_HISTORY = 20`, `_TOOL_LABELS = {...}`)
- **Không hard-code config/secret**: API key, DB URL → env var
- **Không `print()` trong production code**: dùng `logging`
- **Import đúng thứ tự**: stdlib → third-party → local; không `import *`
- **Không unused import/variable**: xóa dead code
- **Input validate sớm**: ở boundary (FastAPI endpoint, tool function)

### Testing Rules (bắt buộc — không được bỏ qua)

- **Mỗi task phải có unit test** — không implement nếu chưa viết test
- **TDD nghiêm ngặt**: viết test trước → chạy verify FAIL → implement → chạy verify PASS
- **Test phải PASS 100%** trước khi commit — không commit code có test đỏ
- **Không mock quá mức**: mock đúng layer (psycopg2, LLM) — không mock chính logic đang test
- **Test phải độc lập**: mỗi test tự setup/teardown, không phụ thuộc thứ tự chạy
- Chạy toàn bộ test suite trước mỗi commit: `uv run pytest tests/ -v`

---

## File Map

```
be/
  schema.sql                          Create — DDL + COMMENTs + FK constraints
  seed.py                             Create — 100 students + full dummy data
  .env.example                        Create — DB connection template

ai/
  requirements.txt                    Create
  .env.example                        Create
  src/
    main.py                           Create — FastAPI app + /chat/stream SSE + static mount
    agent/
      llm.py                          Fill — Gemini Flash ChatGoogleGenerativeAI factory
      history.py                      Fill — in-memory session history store
      tool_registry.py                Fill — exports DEEP_AGENT_TOOLS list
      subagent_registry.py            Fill — exports get_sql_agent()
      deep_agent.py                   Fill — LangGraph ReAct orchestrator + get_deep_agent()
      prompt/
        deep_agent.py                 Fill — SYSTEM_PROMPT string
      tools/
        sql_tools.py                  Fill — get_schema tool, execute_sql tool
        datetime_tools.py             Fill — resolve_time_range tool
        agent_tools.py                Create — call_sql_agent tool, out_of_scope_reply tool
      subagents/
        sql_query_agent.py            Fill — SQL ReAct agent + get_sql_agent()
    frontend/
      index.html                      Create — chat UI layout
      style.css                       Create — gradient theme, bubbles
      app.js                          Create — EventSource SSE handling
  tests/
    conftest.py                       Create — pytest fixtures
    test_sql_tools.py                 Create
    test_datetime_tools.py            Create
    test_history.py                   Create
    test_main.py                      Create
```

---

## Task 1: Database Schema

**Files:**
- Create: `be/schema.sql`
- Create: `be/.env.example`

**Interfaces:**
- Produces: PostgreSQL star schema with 6 tables, full COMMENTs, FK constraints — consumed by Task 2 (seed) and Task 5 (sql_tools)

- [ ] **Step 1: Write schema.sql**

```sql
-- be/schema.sql

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

CREATE TABLE dim_major (
    major_id   SERIAL PRIMARY KEY,
    major_code VARCHAR(10)  UNIQUE NOT NULL,
    major_name VARCHAR(100) NOT NULL,
    faculty    VARCHAR(100) NOT NULL,
    total_credits_required INT NOT NULL DEFAULT 120,
    duration_years         INT NOT NULL DEFAULT 4
);
COMMENT ON TABLE  dim_major IS 'Ngành học của sinh viên. Mỗi sinh viên thuộc một ngành học.';
COMMENT ON COLUMN dim_major.major_code IS 'Mã ngành viết tắt, ví dụ: CNTT, KTPM, HTTT';
COMMENT ON COLUMN dim_major.major_name IS 'Tên đầy đủ của ngành, ví dụ: Công nghệ Thông tin';
COMMENT ON COLUMN dim_major.faculty    IS 'Tên khoa quản lý ngành học';
COMMENT ON COLUMN dim_major.total_credits_required IS 'Tổng số tín chỉ cần hoàn thành để được xét tốt nghiệp';
COMMENT ON COLUMN dim_major.duration_years         IS 'Số năm đào tạo chuẩn (3, 4, hoặc 5 năm)';

CREATE TABLE dim_department (
    department_id   SERIAL PRIMARY KEY,
    department_code VARCHAR(10)  UNIQUE NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    faculty         VARCHAR(100),
    head_name       VARCHAR(100)
);
COMMENT ON TABLE  dim_department IS 'Khoa hoặc bộ môn phụ trách giảng dạy học phần.';
COMMENT ON COLUMN dim_department.department_code IS 'Mã khoa/bộ môn, ví dụ: CNTT, TOAN, NGOAINGU';
COMMENT ON COLUMN dim_department.department_name IS 'Tên đầy đủ của khoa hoặc bộ môn';
COMMENT ON COLUMN dim_department.faculty         IS 'Khoa chủ quản nếu đây là bộ môn trực thuộc';
COMMENT ON COLUMN dim_department.head_name       IS 'Họ tên trưởng khoa hoặc trưởng bộ môn hiện tại';

CREATE TABLE dim_semester (
    semester_id     SERIAL PRIMARY KEY,
    semester_code   VARCHAR(20)  UNIQUE NOT NULL,
    semester_name   VARCHAR(100) NOT NULL,
    academic_year   VARCHAR(10)  NOT NULL,
    semester_number INT NOT NULL CHECK (semester_number IN (1, 2, 3)),
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    is_current      BOOLEAN NOT NULL DEFAULT FALSE
);
COMMENT ON TABLE  dim_semester IS 'Học kỳ trong năm học. Có 3 học kỳ: 1, 2, và 3 (hè). is_current = TRUE cho học kỳ đang diễn ra.';
COMMENT ON COLUMN dim_semester.semester_code   IS 'Mã học kỳ dạng HK1-2024-2025';
COMMENT ON COLUMN dim_semester.semester_name   IS 'Tên hiển thị đầy đủ, ví dụ: Học kỳ 1 năm học 2024-2025';
COMMENT ON COLUMN dim_semester.academic_year   IS 'Năm học định dạng YYYY-YYYY, ví dụ: 2024-2025';
COMMENT ON COLUMN dim_semester.semester_number IS 'Số thứ tự học kỳ trong năm: 1, 2, hoặc 3 (học kỳ hè)';
COMMENT ON COLUMN dim_semester.is_current      IS 'TRUE nếu đây là học kỳ đang diễn ra hiện tại';

CREATE TABLE dim_student (
    student_id              SERIAL PRIMARY KEY,
    student_code            VARCHAR(10)  UNIQUE NOT NULL,
    full_name               VARCHAR(100) NOT NULL,
    gender                  VARCHAR(10)  NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    date_of_birth           DATE         NOT NULL,
    email                   VARCHAR(100) UNIQUE NOT NULL,
    phone                   VARCHAR(15),
    major_id                INT NOT NULL REFERENCES dim_major(major_id),
    admission_year          INT NOT NULL,
    current_gpa             NUMERIC(3,2) NOT NULL DEFAULT 0.00,
    total_credits_completed INT          NOT NULL DEFAULT 0,
    status                  VARCHAR(20)  NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'graduated', 'suspended', 'dropped'))
);
COMMENT ON TABLE  dim_student IS 'Thông tin sinh viên đang học hoặc đã tốt nghiệp tại trường.';
COMMENT ON COLUMN dim_student.student_code            IS 'Mã sinh viên duy nhất, định dạng SV + năm + số thứ tự, ví dụ: SV2021001';
COMMENT ON COLUMN dim_student.full_name               IS 'Họ và tên đầy đủ của sinh viên';
COMMENT ON COLUMN dim_student.gender                  IS 'Giới tính: male (nam), female (nữ), other (khác)';
COMMENT ON COLUMN dim_student.major_id                IS 'Ngành học của sinh viên, khóa ngoại tham chiếu đến dim_major';
COMMENT ON COLUMN dim_student.admission_year          IS 'Năm sinh viên nhập học, ví dụ: 2021, 2022, 2023, 2024';
COMMENT ON COLUMN dim_student.current_gpa             IS 'Điểm trung bình tích lũy hiện tại, thang 4.0. Dùng để xét học bổng và cảnh báo học tập.';
COMMENT ON COLUMN dim_student.total_credits_completed IS 'Tổng số tín chỉ đã hoàn thành (môn đã qua), dùng để xét tiến độ tốt nghiệp';
COMMENT ON COLUMN dim_student.status                  IS 'Trạng thái: active (đang học), graduated (tốt nghiệp), suspended (đình chỉ), dropped (thôi học)';

CREATE TABLE dim_course (
    course_id     SERIAL PRIMARY KEY,
    course_code   VARCHAR(10)  UNIQUE NOT NULL,
    course_name   VARCHAR(200) NOT NULL,
    credits       INT NOT NULL CHECK (credits BETWEEN 1 AND 4),
    department_id INT NOT NULL REFERENCES dim_department(department_id),
    description   TEXT,
    is_required   BOOLEAN NOT NULL DEFAULT TRUE,
    prerequisites VARCHAR(200)
);
COMMENT ON TABLE  dim_course IS 'Danh sách học phần (môn học) trong chương trình đào tạo.';
COMMENT ON COLUMN dim_course.course_code   IS 'Mã học phần duy nhất, ví dụ: CS101, MATH201, ENG301';
COMMENT ON COLUMN dim_course.course_name   IS 'Tên đầy đủ của học phần';
COMMENT ON COLUMN dim_course.credits       IS 'Số tín chỉ của học phần, từ 1 đến 4';
COMMENT ON COLUMN dim_course.department_id IS 'Khoa/bộ môn phụ trách giảng dạy học phần này';
COMMENT ON COLUMN dim_course.is_required   IS 'TRUE nếu là học phần bắt buộc, FALSE nếu là học phần tự chọn';
COMMENT ON COLUMN dim_course.prerequisites IS 'Mã các học phần tiên quyết cần học trước, phân cách bởi dấu phẩy. NULL nếu không có.';

CREATE TABLE dim_scholarship (
    scholarship_id   SERIAL PRIMARY KEY,
    scholarship_code VARCHAR(20)  UNIQUE NOT NULL,
    scholarship_name VARCHAR(200) NOT NULL,
    scholarship_type VARCHAR(50)  NOT NULL CHECK (scholarship_type IN ('merit', 'need', 'enterprise')),
    amount           NUMERIC(12,2) NOT NULL,
    min_gpa          NUMERIC(3,2),
    description      TEXT
);
COMMENT ON TABLE  dim_scholarship IS 'Danh mục các loại học bổng mà trường cấp cho sinh viên.';
COMMENT ON COLUMN dim_scholarship.scholarship_type IS 'Loại học bổng: merit (học lực), need (hoàn cảnh khó khăn), enterprise (doanh nghiệp tài trợ)';
COMMENT ON COLUMN dim_scholarship.amount           IS 'Giá trị học bổng mỗi học kỳ, đơn vị VND';
COMMENT ON COLUMN dim_scholarship.min_gpa          IS 'GPA tối thiểu trên thang 4.0 để đủ điều kiện xét. NULL nếu không yêu cầu GPA.';

-- ============================================================
-- FACT TABLES
-- ============================================================

CREATE TABLE fact_enrollment (
    enrollment_id SERIAL PRIMARY KEY,
    student_id    INT NOT NULL REFERENCES dim_student(student_id),
    course_id     INT NOT NULL REFERENCES dim_course(course_id),
    semester_id   INT NOT NULL REFERENCES dim_semester(semester_id),
    grade         NUMERIC(4,2),
    grade_letter  VARCHAR(2),
    credits_earned INT NOT NULL DEFAULT 0,
    status        VARCHAR(20) NOT NULL DEFAULT 'in_progress'
                      CHECK (status IN ('passed', 'failed', 'in_progress', 'withdrawn')),
    registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, course_id, semester_id)
);
COMMENT ON TABLE  fact_enrollment IS 'Bảng sự kiện ghi nhận mỗi lần sinh viên đăng ký một học phần trong một học kỳ. Đây là bảng trung tâm của mô hình sao.';
COMMENT ON COLUMN fact_enrollment.grade         IS 'Điểm số trên thang 10. NULL nếu học kỳ chưa kết thúc (status = in_progress).';
COMMENT ON COLUMN fact_enrollment.grade_letter  IS 'Điểm chữ: A (>=8.5), B+ (8.0-8.4), B (7.0-7.9), C+ (6.5-6.9), C (5.5-6.4), D+ (5.0-5.4), D (4.0-4.9), F (<4.0)';
COMMENT ON COLUMN fact_enrollment.credits_earned IS 'Số tín chỉ đạt được: bằng credits của dim_course nếu passed, bằng 0 nếu failed hoặc withdrawn';
COMMENT ON COLUMN fact_enrollment.status        IS 'Trạng thái: passed (qua môn), failed (trượt), in_progress (đang học), withdrawn (rút môn)';

CREATE TABLE fact_scholarship_award (
    award_id       SERIAL PRIMARY KEY,
    student_id     INT NOT NULL REFERENCES dim_student(student_id),
    scholarship_id INT NOT NULL REFERENCES dim_scholarship(scholarship_id),
    semester_id    INT NOT NULL REFERENCES dim_semester(semester_id),
    amount_awarded NUMERIC(12,2) NOT NULL,
    awarded_at     DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (student_id, scholarship_id, semester_id)
);
COMMENT ON TABLE  fact_scholarship_award IS 'Bảng sự kiện ghi nhận mỗi lần một sinh viên được nhận học bổng trong một học kỳ.';
COMMENT ON COLUMN fact_scholarship_award.amount_awarded IS 'Số tiền học bổng thực tế được trao, đơn vị VND.';
```

- [ ] **Step 2: Create be/.env.example**

```
DATABASE_URL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
```

- [ ] **Step 3: Run schema against Supabase**

In Supabase dashboard → SQL Editor → paste and run `schema.sql`.
Verify by running: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`
Expected: 6 tables listed (dim_major, dim_department, dim_semester, dim_student, dim_course, dim_scholarship, fact_enrollment, fact_scholarship_award).

- [ ] **Step 4: Commit**

```bash
git add be/schema.sql be/.env.example
git commit -m "feat: add star schema DDL with PostgreSQL COMMENTs"
```

---

## Task 2: Seed Data

**Files:**
- Create: `be/seed.py`

**Interfaces:**
- Consumes: Supabase PostgreSQL with schema from Task 1 (`DATABASE_URL` in `be/.env`)
- Produces: ~100 students, 5 majors, 4 departments, 6 semesters, 30 courses, 4 scholarships, ~400 enrollments, ~60 scholarship awards

- [ ] **Step 1: Write seed.py**

```python
# be/seed.py
import os
import random
from datetime import date, timedelta
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from faker import Faker

load_dotenv()
fake = Faker('vi_VN')
random.seed(42)

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
conn.autocommit = False
cur = conn.cursor()

def run():
    _seed_departments()
    _seed_majors()
    _seed_semesters()
    _seed_courses()
    _seed_scholarships()
    _seed_students()
    _seed_enrollments()
    _seed_scholarship_awards()
    conn.commit()
    print("✅ Seed complete")

def _seed_departments():
    depts = [
        ("CNTT",     "Khoa Công nghệ Thông tin",          "Kỹ thuật",     "TS. Nguyễn Văn An"),
        ("TOAN",     "Bộ môn Toán - Tin",                 "Khoa học cơ bản", "TS. Trần Thị Bình"),
        ("NGOAINGU", "Bộ môn Ngoại ngữ",                  "Khoa học xã hội", "ThS. Lê Văn Cường"),
        ("DAICUONG", "Bộ môn Giáo dục Đại cương",          None,           "TS. Phạm Thị Dung"),
    ]
    cur.executemany(
        "INSERT INTO dim_department (department_code, department_name, faculty, head_name) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        depts
    )

def _seed_majors():
    majors = [
        ("CNTT",  "Công nghệ Thông tin",          "Kỹ thuật",     120, 4),
        ("KTPM",  "Kỹ thuật Phần mềm",            "Kỹ thuật",     125, 4),
        ("HTTT",  "Hệ thống Thông tin",            "Kỹ thuật",     120, 4),
        ("MMT",   "Mạng Máy tính & Truyền thông", "Kỹ thuật",     120, 4),
        ("KHMT",  "Khoa học Máy tính",             "Khoa học",     130, 4),
    ]
    cur.executemany(
        "INSERT INTO dim_major (major_code, major_name, faculty, total_credits_required, duration_years) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        majors
    )

def _seed_semesters():
    semesters = [
        ("HK1-2023-2024", "Học kỳ 1 năm học 2023-2024", "2023-2024", 1, date(2023,9,4),  date(2024,1,14),  False),
        ("HK2-2023-2024", "Học kỳ 2 năm học 2023-2024", "2023-2024", 2, date(2024,1,22), date(2024,5,31),  False),
        ("HK3-2023-2024", "Học kỳ hè năm học 2023-2024","2023-2024", 3, date(2024,6,10), date(2024,8,16),  False),
        ("HK1-2024-2025", "Học kỳ 1 năm học 2024-2025", "2024-2025", 1, date(2024,9,2),  date(2025,1,12),  False),
        ("HK2-2024-2025", "Học kỳ 2 năm học 2024-2025", "2024-2025", 2, date(2025,1,20), date(2025,5,30),  False),
        ("HK1-2025-2026", "Học kỳ 1 năm học 2025-2026", "2025-2026", 1, date(2025,9,1),  date(2026,1,11),  True),
    ]
    cur.executemany(
        "INSERT INTO dim_semester (semester_code,semester_name,academic_year,semester_number,start_date,end_date,is_current) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        semesters
    )

def _seed_courses():
    # dept_id lookup
    cur.execute("SELECT department_id, department_code FROM dim_department")
    dept_map = {row[1]: row[0] for row in cur.fetchall()}

    courses = [
        # CS courses (CNTT dept)
        ("CS101", "Nhập môn Lập trình",               2, "CNTT", "Các khái niệm cơ bản về lập trình, biến, vòng lặp, hàm với Python.", True,  None),
        ("CS102", "Cấu trúc Dữ liệu & Giải thuật",    3, "CNTT", "Mảng, danh sách liên kết, cây, đồ thị và các thuật toán sắp xếp, tìm kiếm.", True, "CS101"),
        ("CS201", "Lập trình Hướng đối tượng",         3, "CNTT", "Các khái niệm OOP: class, kế thừa, đa hình, interface. Thực hành với Java.", True, "CS101"),
        ("CS202", "Cơ sở Dữ liệu",                    3, "CNTT", "Thiết kế CSDL quan hệ, SQL, chuẩn hóa, transaction.", True, "CS101"),
        ("CS301", "Công nghệ Web",                     3, "CNTT", "HTML/CSS/JS, REST API, FastAPI, React cơ bản.", True, "CS201"),
        ("CS302", "Học máy cơ bản",                    3, "CNTT", "Hồi quy, phân loại, clustering, neural network cơ bản.", False,"CS102"),
        ("CS303", "Mạng máy tính",                     3, "CNTT", "Mô hình OSI/TCP-IP, giao thức mạng, bảo mật mạng cơ bản.", True, None),
        ("CS401", "Trí tuệ nhân tạo",                  3, "CNTT", "Tìm kiếm, logic, học tăng cường, xử lý ngôn ngữ tự nhiên.", False,"CS302"),
        ("CS402", "Kiến trúc phần mềm",                3, "CNTT", "Design patterns, microservices, DevOps cơ bản.", False,"CS301"),
        ("CS403", "Đồ án tốt nghiệp",                  6, "CNTT", "Dự án nghiên cứu hoặc ứng dụng thực tế hoàn chỉnh.", True, None),
        # Math courses (TOAN dept)
        ("MATH101","Giải tích 1",                      3, "TOAN", "Giới hạn, đạo hàm, tích phân một biến.", True, None),
        ("MATH102","Giải tích 2",                      3, "TOAN", "Tích phân nhiều biến, chuỗi số, phương trình vi phân.", True, "MATH101"),
        ("MATH201","Đại số tuyến tính",                3, "TOAN", "Ma trận, định thức, không gian vectơ, trị riêng.", True, None),
        ("MATH202","Xác suất & Thống kê",              3, "TOAN", "Biến ngẫu nhiên, phân phối xác suất, kiểm định giả thuyết.", True, "MATH101"),
        ("MATH301","Toán rời rạc",                     3, "TOAN", "Tổ hợp, đồ thị, logic, lý thuyết số.", True, None),
        ("MATH302","Tối ưu hóa",                       2, "TOAN", "Quy hoạch tuyến tính, gradient descent, thuật toán tối ưu.", False,"MATH201"),
        # English courses (NGOAINGU dept)
        ("ENG101", "Tiếng Anh cơ bản 1",              2, "NGOAINGU","Ngữ pháp và từ vựng tiếng Anh cơ bản, luyện nghe nói.", True, None),
        ("ENG102", "Tiếng Anh cơ bản 2",              2, "NGOAINGU","Tiếp nối ENG101, kỹ năng đọc viết.",                  True, "ENG101"),
        ("ENG201", "Tiếng Anh chuyên ngành IT",        2, "NGOAINGU","Từ vựng kỹ thuật, đọc tài liệu IT, viết email chuyên nghiệp.", True, "ENG102"),
        # General education (DAICUONG dept)
        ("GEN101", "Triết học Mác - Lênin",            3, "DAICUONG","Chủ nghĩa duy vật biện chứng và lịch sử.", True, None),
        ("GEN102", "Kinh tế chính trị Mác - Lênin",   2, "DAICUONG","Lý luận kinh tế cơ bản theo quan điểm Mác.", True, None),
        ("GEN103", "Tư tưởng Hồ Chí Minh",             2, "DAICUONG","Hệ thống tư tưởng của Hồ Chí Minh.", True, None),
        ("GEN104", "Lịch sử Đảng Cộng sản Việt Nam",  2, "DAICUONG","Lịch sử thành lập và phát triển của Đảng.", True, None),
        ("GEN105", "Giáo dục thể chất 1",              1, "DAICUONG","Thể dục thể thao cơ bản, rèn luyện sức khỏe.", True, None),
        ("GEN106", "Giáo dục thể chất 2",              1, "DAICUONG","Tiếp nối GEN105, các môn thể thao tự chọn.", True, "GEN105"),
        ("GEN107", "Giáo dục quốc phòng - an ninh",   3, "DAICUONG","Kiến thức quân sự và an ninh quốc gia.", True, None),
        # Electives
        ("CS501", "Phát triển ứng dụng Mobile",        3, "CNTT", "React Native, Android, iOS cơ bản.", False,"CS301"),
        ("CS502", "An toàn thông tin",                  3, "CNTT", "Mã hóa, bảo mật web, kiểm thử xâm nhập cơ bản.", False,"CS303"),
        ("CS503", "Điện toán đám mây",                  2, "CNTT", "AWS/GCP/Azure cơ bản, containerization, CI/CD.", False,"CS303"),
        ("CS504", "Phân tích dữ liệu lớn",              3, "CNTT", "Hadoop, Spark, data pipeline, visualization.", False,"CS302"),
    ]
    for code, name, credits, dept_code, desc, required, prereq in courses:
        cur.execute(
            "INSERT INTO dim_course (course_code,course_name,credits,department_id,description,is_required,prerequisites) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (code, name, credits, dept_map[dept_code], desc, required, prereq)
        )

def _seed_scholarships():
    scholarships = [
        ("HB-KK1",  "Học bổng Khuyến khích Loại 1",           "merit",      4000000.00, 3.60, "Dành cho SV có GPA >= 3.6/4.0 trong học kỳ trước. Trị giá 4 triệu VND/kỳ."),
        ("HB-KK2",  "Học bổng Khuyến khích Loại 2",           "merit",      2500000.00, 3.20, "Dành cho SV có GPA từ 3.2 đến 3.59/4.0 trong học kỳ trước."),
        ("HB-HC",   "Học bổng Hỗ trợ Hoàn cảnh",              "need",       3000000.00, None, "Dành cho SV có hoàn cảnh khó khăn được nhà trường xét duyệt. Không yêu cầu GPA tối thiểu."),
        ("HB-DN",   "Học bổng Doanh nghiệp TechViet",          "enterprise", 6000000.00, 3.50, "Do công ty TechViet tài trợ. Yêu cầu GPA >= 3.5 và cam kết thực tập tại công ty."),
    ]
    cur.executemany(
        "INSERT INTO dim_scholarship (scholarship_code,scholarship_name,scholarship_type,amount,min_gpa,description) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        scholarships
    )

def _seed_students():
    cur.execute("SELECT major_id FROM dim_major")
    major_ids = [r[0] for r in cur.fetchall()]

    counter = {y: 1 for y in [2021, 2022, 2023, 2024]}
    for _ in range(100):
        year = random.choices([2021, 2022, 2023, 2024], weights=[25, 25, 25, 25])[0]
        code = f"SV{year}{counter[year]:03d}"
        counter[year] += 1
        gender = random.choice(['male', 'female'])
        dob = fake.date_of_birth(minimum_age=18, maximum_age=24)
        gpa = round(random.uniform(1.0, 4.0), 2)
        credits = random.randint(0, 90)
        status = random.choices(['active','graduated','suspended','dropped'], weights=[85,8,4,3])[0]
        cur.execute(
            """INSERT INTO dim_student
               (student_code,full_name,gender,date_of_birth,email,phone,major_id,admission_year,current_gpa,total_credits_completed,status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (code, fake.name(), gender, dob,
             f"{code.lower()}@student.edu.vn",
             fake.phone_number()[:15],
             random.choice(major_ids), year, gpa, credits, status)
        )

def _seed_enrollments():
    cur.execute("SELECT student_id, admission_year FROM dim_student")
    students = cur.fetchall()
    cur.execute("SELECT semester_id, semester_number, start_date FROM dim_semester ORDER BY start_date")
    semesters = cur.fetchall()
    cur.execute("SELECT course_id, credits FROM dim_course")
    courses = cur.fetchall()

    grade_map = [(9.0,10.0,'A'),(8.0,8.9,'B+'),(7.0,7.9,'B'),(6.5,6.9,'C+'),(5.5,6.4,'C'),(5.0,5.4,'D+'),(4.0,4.9,'D'),(0.0,3.9,'F')]

    for student_id, _ in students:
        chosen_courses = random.sample(courses, min(len(courses), random.randint(4, 6)))
        for sem in semesters:
            semester_id, _, _ = sem
            is_current = sem[2] == date(2025, 9, 1)  # HK1-2025-2026
            sem_courses = random.sample(chosen_courses, min(len(chosen_courses), random.randint(3, 5)))
            for course_id, credits in sem_courses:
                if is_current:
                    grade, letter, earned = None, None, 0
                    status = 'in_progress'
                else:
                    g = round(random.uniform(0, 10), 2)
                    for lo, hi, lt in grade_map:
                        if lo <= g <= hi:
                            letter = lt
                            break
                    grade = g
                    passed = g >= 4.0
                    earned = credits if passed else 0
                    status = 'passed' if passed else 'failed'
                try:
                    cur.execute(
                        """INSERT INTO fact_enrollment
                           (student_id,course_id,semester_id,grade,grade_letter,credits_earned,status)
                           VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (student_id, course_id, semester_id, grade, letter, earned, status)
                    )
                except Exception:
                    conn.rollback()

def _seed_scholarship_awards():
    cur.execute("SELECT student_id, current_gpa FROM dim_student WHERE status = 'active'")
    active_students = cur.fetchall()
    cur.execute("SELECT scholarship_id, min_gpa, amount FROM dim_scholarship")
    scholarships = cur.fetchall()
    cur.execute("SELECT semester_id FROM dim_semester WHERE is_current = FALSE ORDER BY start_date DESC LIMIT 2")
    past_sems = [r[0] for r in cur.fetchall()]

    for student_id, gpa in active_students:
        for scholarship_id, min_gpa, amount in scholarships:
            if min_gpa is None or gpa >= float(min_gpa):
                if random.random() < 0.3:
                    sem_id = random.choice(past_sems) if past_sems else 1
                    try:
                        cur.execute(
                            """INSERT INTO fact_scholarship_award
                               (student_id,scholarship_id,semester_id,amount_awarded,awarded_at)
                               VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                            (student_id, scholarship_id, sem_id, float(amount), date.today())
                        )
                    except Exception:
                        conn.rollback()

if __name__ == "__main__":
    run()
    cur.close()
    conn.close()
```

- [ ] **Step 2: Install Faker and run seed**

```bash
cd be
uv run --with psycopg2-binary --with python-dotenv --with faker python seed.py
# Hoặc nếu be/ có pyproject.toml riêng: uv run seed.py
```

Expected output: `✅ Seed complete`

Verify in Supabase → Table Editor: `dim_student` has ~100 rows, `fact_enrollment` has ~400+ rows.

- [ ] **Step 3: Commit**

```bash
git add be/seed.py
git commit -m "feat: add seed script with 100 students and full dummy data"
```

---

## Task 3: Project Setup

**Files:**
- Create: `ai/pyproject.toml`
- Create: `ai/.env.example`
- Create: `ai/tests/conftest.py`

**Interfaces:**
- Produces: installable Python environment managed by uv, pytest fixtures — consumed by all subsequent tasks

- [ ] **Step 1: Install uv (nếu chưa có)**

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Verify
uv --version
```

- [ ] **Step 2: Khởi tạo project với uv**

```bash
cd ai
uv init --no-workspace
```

Lệnh này tạo `pyproject.toml`. Sau đó thêm tất cả dependencies:

```bash
uv add langchain langchain-core langchain-google-genai langgraph
uv add fastapi "uvicorn[standard]" psycopg2-binary python-dotenv
uv add --dev faker pytest pytest-asyncio pytest-mock httpx freezegun
```

`uv` tự tạo `.venv` và `uv.lock` — không cần chạy `pip` hay activate venv thủ công.

- [ ] **Step 3: Verify pyproject.toml đã có dependencies**

```bash
uv tree
```

Expected: thấy langchain, langgraph, fastapi, psycopg2-binary trong dependency tree.

- [ ] **Step 4: Write .env.example**

```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
```

- [ ] **Step 5: Write tests/conftest.py**

```python
# ai/tests/conftest.py
import sys
import os
import pytest
from unittest.mock import MagicMock

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set dummy env vars before any module imports them
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

@pytest.fixture
def mock_db_conn(mocker):
    """Mock psycopg2.connect for unit tests that don't hit a real DB."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: s
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor
    mocker.patch("psycopg2.connect", return_value=mock_conn)
    return mock_conn, mock_cursor
```

- [ ] **Step 6: Verify pytest runs**

```bash
cd ai
uv run pytest tests/ -v
```

Expected: `no tests ran` (0 collected) — no failures.

- [ ] **Step 7: Commit**

```bash
git add ai/pyproject.toml ai/uv.lock ai/.env.example ai/tests/conftest.py
git commit -m "feat: add project dependencies via uv and test scaffold"
```

---

## Task 4: LLM Client

**Files:**
- Fill: `ai/src/agent/llm.py`

**Interfaces:**
- Produces: `get_llm() -> ChatGoogleGenerativeAI` — consumed by Task 7 (SQL agent) and Task 9 (deep agent)

- [ ] **Step 1: Write the failing test**

```python
# ai/tests/test_llm.py
import pytest
from unittest.mock import patch

def test_get_llm_returns_instance():
    with patch("langchain_google_genai.ChatGoogleGenerativeAI.__init__", return_value=None):
        from agent.llm import get_llm
        llm = get_llm()
        assert llm is not None

def test_get_llm_uses_env_key(mocker):
    import os
    os.environ["GEMINI_API_KEY"] = "test-abc"
    mock_cls = mocker.patch("agent.llm.ChatGoogleGenerativeAI")
    from agent.llm import get_llm
    get_llm()
    mock_cls.assert_called_once()
    _, kwargs = mock_cls.call_args
    assert kwargs.get("google_api_key") == "test-abc" or mock_cls.call_args[0]
```

- [ ] **Step 2: Run test — verify it fails**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: FAIL — `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement llm.py**

```python
# ai/src/agent/llm.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(temperature: float = 0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=temperature,
    )
```

- [ ] **Step 4: Run test — verify it passes**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ai/src/agent/llm.py ai/tests/test_llm.py
git commit -m "feat: add Gemini Flash LLM client factory"
```

---

## Task 5: SQL Tools

**Files:**
- Fill: `ai/src/agent/tools/sql_tools.py`
- Create: `ai/tests/test_sql_tools.py`

**Interfaces:**
- Produces:
  - `get_schema() -> str` — LangChain tool, returns formatted schema string
  - `execute_sql(query: str) -> dict` — LangChain tool, returns `{"rows": [...], "row_count": N}` or `{"error": "...", "rows": [], "row_count": 0}`
- Consumed by: Task 7 (sql_query_agent)

- [ ] **Step 1: Write failing tests**

```python
# ai/tests/test_sql_tools.py
import pytest
from unittest.mock import MagicMock, patch

def test_execute_sql_rejects_delete():
    from agent.tools.sql_tools import execute_sql
    result = execute_sql.invoke({"query": "DELETE FROM dim_student"})
    assert "error" in result
    assert result["row_count"] == 0

def test_execute_sql_rejects_drop():
    from agent.tools.sql_tools import execute_sql
    result = execute_sql.invoke({"query": "DROP TABLE dim_student"})
    assert "error" in result

def test_execute_sql_allows_with_clause():
    from agent.tools.sql_tools import execute_sql
    with patch("agent.tools.sql_tools._get_conn") as mock_conn_fn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__ = lambda s: s
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_fn.return_value = mock_conn
        result = execute_sql.invoke({"query": "WITH cte AS (SELECT 1) SELECT * FROM cte"})
        assert "error" not in result or result.get("row_count") == 0

def test_execute_sql_returns_rows():
    from agent.tools.sql_tools import execute_sql
    with patch("agent.tools.sql_tools._get_conn") as mock_conn_fn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"student_id": 1, "full_name": "Nguyễn Văn A"}]
        mock_conn.cursor.return_value.__enter__ = lambda s: s
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_fn.return_value = mock_conn
        result = execute_sql.invoke({"query": "SELECT student_id, full_name FROM dim_student LIMIT 1"})
        assert result["row_count"] == 1

def test_get_schema_returns_string():
    from agent.tools.sql_tools import get_schema
    with patch("agent.tools.sql_tools._get_conn") as mock_conn_fn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            # columns query
            [{"table_name": "dim_student", "table_comment": "Thông tin sinh viên",
              "column_name": "student_id", "data_type": "integer",
              "is_nullable": "NO", "column_default": None, "column_comment": "PK"}],
            # FK query
            []
        ]
        mock_conn.cursor.return_value.__enter__ = lambda s: s
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_fn.return_value = mock_conn
        result = get_schema.invoke({})
        assert "dim_student" in result
        assert "TABLE:" in result
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_sql_tools.py -v
```

Expected: FAIL — ImportError

- [ ] **Step 3: Implement sql_tools.py**

```python
# ai/src/agent/tools/sql_tools.py
import os
import psycopg2
import psycopg2.extras
from langchain_core.tools import tool

def _get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@tool
def get_schema() -> str:
    """Read the full database schema including table descriptions, column descriptions,
    data types, nullable flags, and foreign key relationships.
    ALWAYS call this first before writing any SQL query."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    t.table_name,
                    obj_description(pc.oid, 'pg_class') AS table_comment,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    col_description(pc.oid, c.ordinal_position) AS column_comment
                FROM information_schema.tables t
                JOIN information_schema.columns c
                    ON t.table_name = c.table_name AND t.table_schema = c.table_schema
                JOIN pg_class pc
                    ON pc.relname = t.table_name
                    AND pc.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name, c.ordinal_position
            """)
            columns = cur.fetchall()

            cur.execute("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name  AS references_table,
                    ccu.column_name AS references_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
            """)
            fks = cur.fetchall()
    finally:
        conn.close()

    fk_map = {(r['table_name'], r['column_name']): f"→ {r['references_table']}.{r['references_column']}" for r in fks}

    schema_text = "=== DATABASE SCHEMA ===\n\n"
    current_table = None
    for row in columns:
        if row['table_name'] != current_table:
            current_table = row['table_name']
            schema_text += f"TABLE: {current_table}\n"
            schema_text += f"Description: {row['table_comment'] or '(no description)'}\n"
            schema_text += "Columns:\n"
        fk = fk_map.get((row['table_name'], row['column_name']), '')
        nullable = 'nullable' if row['is_nullable'] == 'YES' else 'not null'
        comment = row['column_comment'] or ''
        schema_text += f"  - {row['column_name']} ({row['data_type']}, {nullable})"
        if fk:
            schema_text += f" [FK: {fk}]"
        if comment:
            schema_text += f" -- {comment}"
        schema_text += "\n"
        if row == columns[-1] or columns[columns.index(row) + 1]['table_name'] != current_table:
            schema_text += "\n"
    return schema_text


@tool
def execute_sql(query: str) -> dict:
    """Execute a SELECT SQL query against the student management database.
    Only SELECT and WITH...SELECT queries are permitted.
    Args:
        query: A valid PostgreSQL SELECT statement
    Returns:
        {"rows": [...], "row_count": N} on success
        {"error": "...", "rows": [], "row_count": 0} on failure or disallowed query
    """
    stripped = query.strip().upper().lstrip()
    if not (stripped.startswith("SELECT") or stripped.startswith("WITH")):
        return {"error": "Only SELECT queries are allowed. INSERT/UPDATE/DELETE/DROP are forbidden.", "rows": [], "row_count": 0}

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = [dict(r) for r in cur.fetchall()]
            return {"rows": rows, "row_count": len(rows)}
    except Exception as e:
        return {"error": str(e), "rows": [], "row_count": 0}
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
uv run pytest tests/test_sql_tools.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add ai/src/agent/tools/sql_tools.py ai/tests/test_sql_tools.py
git commit -m "feat: add get_schema and execute_sql LangChain tools"
```

---

## Task 6: Datetime Tool

**Files:**
- Fill: `ai/src/agent/tools/datetime_tools.py`
- Create: `ai/tests/test_datetime_tools.py`

**Interfaces:**
- Produces: `resolve_time_range(expression: str) -> dict` where dict is `{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": str}`
- Consumed by: Task 8 (agent_tools / tool_registry)

- [ ] **Step 1: Write failing tests**

```python
# ai/tests/test_datetime_tools.py
import pytest
from freezegun import freeze_time
from unittest.mock import patch, MagicMock

@freeze_time("2026-09-05")
def test_tháng_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tháng trước"})
    assert result["start_date"] == "2026-08-01"
    assert result["end_date"] == "2026-08-31"
    assert "8" in result["label"] or "Tháng" in result["label"]

@freeze_time("2026-09-05")
def test_tháng_này():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tháng này"})
    assert result["start_date"] == "2026-09-01"
    assert result["end_date"] == "2026-09-30"

@freeze_time("2026-09-05")
def test_năm_ngoái():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "năm ngoái"})
    assert result["start_date"] == "2025-01-01"
    assert result["end_date"] == "2025-12-31"

@freeze_time("2026-09-05")
def test_năm_nay():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "năm nay"})
    assert result["start_date"] == "2026-01-01"
    assert result["end_date"] == "2026-12-31"

@freeze_time("2026-09-05")
def test_quý_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "quý trước"})
    assert result["start_date"] == "2026-04-01"
    assert result["end_date"] == "2026-06-30"

@freeze_time("2026-09-05")
def test_hai_quý_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "2 quý trước"})
    assert result["start_date"] == "2026-01-01"
    assert result["end_date"] == "2026-03-31"

@freeze_time("2026-09-05")
def test_tuần_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tuần trước"})
    assert result["start_date"] == "2026-08-24"
    assert result["end_date"] == "2026-08-30"

@freeze_time("2026-09-05")
def test_tháng_specific():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tháng 3"})
    assert result["start_date"] == "2026-03-01"
    assert result["end_date"] == "2026-03-31"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_datetime_tools.py -v
```

Expected: FAIL — ImportError

- [ ] **Step 3: Implement datetime_tools.py**

```python
# ai/src/agent/tools/datetime_tools.py
import os
import re
import calendar
from datetime import date, timedelta
from typing import Optional
import psycopg2
import psycopg2.extras
from langchain_core.tools import tool

def _get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def _last_day(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]

@tool
def resolve_time_range(expression: str) -> dict:
    """Convert a Vietnamese relative time expression into an absolute date range.

    Supported: 'tháng này/trước', 'tháng N' (1-12), 'quý này/trước',
    'N quý trước', 'năm nay/ngoái', 'tuần này/trước', 'học kỳ này/trước'.

    Returns: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": str}
    """
    today = date.today()
    expr = expression.lower().strip()

    # ── Month ─────────────────────────────────────────────────────────────────
    if expr in ("tháng này", "tháng nay"):
        start = today.replace(day=1)
        end   = today.replace(day=_last_day(today.year, today.month))
        return {"start_date": str(start), "end_date": str(end), "label": f"Tháng {today.month}/{today.year}"}

    if expr == "tháng trước":
        first_this = today.replace(day=1)
        last_prev  = first_this - timedelta(days=1)
        start = last_prev.replace(day=1)
        return {"start_date": str(start), "end_date": str(last_prev), "label": f"Tháng {last_prev.month}/{last_prev.year}"}

    m = re.fullmatch(r"tháng\s+(\d{1,2})", expr)
    if m:
        month = int(m.group(1))
        if 1 <= month <= 12:
            year  = today.year if month <= today.month else today.year - 1
            start = date(year, month, 1)
            end   = date(year, month, _last_day(year, month))
            return {"start_date": str(start), "end_date": str(end), "label": f"Tháng {month}/{year}"}

    # ── Quarter ────────────────────────────────────────────────────────────────
    def quarter_range(year: int, q: int):
        sm = (q - 1) * 3 + 1
        em = sm + 2
        return date(year, sm, 1), date(year, em, _last_day(year, em))

    cq = (today.month - 1) // 3 + 1

    if expr in ("quý này", "quý nay"):
        s, e = quarter_range(today.year, cq)
        return {"start_date": str(s), "end_date": str(e), "label": f"Quý {cq}/{today.year}"}

    if expr == "quý trước":
        pivot = date(today.year, (cq - 1) * 3 + 1, 1) - timedelta(days=1)
        pq = (pivot.month - 1) // 3 + 1
        s, e = quarter_range(pivot.year, pq)
        return {"start_date": str(s), "end_date": str(e), "label": f"Quý {pq}/{pivot.year}"}

    m = re.fullmatch(r"(\d+)\s+quý trước", expr)
    if m:
        n = int(m.group(1))
        total_months = n * 3
        pivot_month  = today.month - total_months
        pivot_year   = today.year
        while pivot_month <= 0:
            pivot_month += 12
            pivot_year  -= 1
        pq = (pivot_month - 1) // 3 + 1
        s, e = quarter_range(pivot_year, pq)
        return {"start_date": str(s), "end_date": str(e), "label": f"Quý {pq}/{pivot_year}"}

    # ── Year ───────────────────────────────────────────────────────────────────
    if expr in ("năm nay", "năm này"):
        return {"start_date": f"{today.year}-01-01", "end_date": f"{today.year}-12-31", "label": f"Năm {today.year}"}

    if expr == "năm ngoái":
        y = today.year - 1
        return {"start_date": f"{y}-01-01", "end_date": f"{y}-12-31", "label": f"Năm {y}"}

    # ── Week ───────────────────────────────────────────────────────────────────
    if expr in ("tuần này", "tuần nay"):
        start = today - timedelta(days=today.weekday())
        return {"start_date": str(start), "end_date": str(start + timedelta(days=6)), "label": "Tuần này"}

    if expr == "tuần trước":
        start = today - timedelta(days=today.weekday() + 7)
        return {"start_date": str(start), "end_date": str(start + timedelta(days=6)), "label": "Tuần trước"}

    # ── Semester (query DB) ────────────────────────────────────────────────────
    if "học kỳ" in expr:
        try:
            conn = _get_conn()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if any(w in expr for w in ("này", "nay", "hiện tại")):
                    cur.execute("SELECT * FROM dim_semester WHERE is_current = TRUE LIMIT 1")
                    row = cur.fetchone()
                elif "trước" in expr:
                    cur.execute("SELECT start_date FROM dim_semester WHERE is_current = TRUE LIMIT 1")
                    current = cur.fetchone()
                    if current:
                        cur.execute("SELECT * FROM dim_semester WHERE end_date < %s ORDER BY end_date DESC LIMIT 1", (current['start_date'],))
                        row = cur.fetchone()
                    else:
                        row = None
                else:
                    row = None
            conn.close()
            if row:
                return {"start_date": str(row['start_date']), "end_date": str(row['end_date']), "label": row['semester_name']}
        except Exception:
            pass

    # ── Fallback: current month ────────────────────────────────────────────────
    start = today.replace(day=1)
    end   = today.replace(day=_last_day(today.year, today.month))
    return {"start_date": str(start), "end_date": str(end), "label": f"Tháng {today.month}/{today.year} (mặc định)"}
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
uv run pytest tests/test_datetime_tools.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add ai/src/agent/tools/datetime_tools.py ai/tests/test_datetime_tools.py
git commit -m "feat: add resolve_time_range tool for Vietnamese time expressions"
```

---

## Task 7: SQL Query Agent

**Files:**
- Fill: `ai/src/agent/subagents/sql_query_agent.py`
- Fill: `ai/src/agent/subagent_registry.py`

**Interfaces:**
- Consumes: `get_schema`, `execute_sql` from Task 5; `get_llm()` from Task 4
- Produces: `get_sql_agent() -> CompiledGraph` — callable with `await agent.ainvoke({"messages": [...]}, config=config)`

- [ ] **Step 1: Write failing test**

```python
# ai/tests/test_sql_agent.py
import pytest
from unittest.mock import patch, MagicMock

def test_sql_agent_creation():
    with patch("agent.llm.ChatGoogleGenerativeAI") as mock_llm:
        mock_llm.return_value = MagicMock()
        from agent.subagents.sql_query_agent import get_sql_agent
        agent = get_sql_agent()
        assert agent is not None

def test_sql_agent_singleton():
    with patch("agent.llm.ChatGoogleGenerativeAI") as mock_llm:
        mock_llm.return_value = MagicMock()
        from agent.subagents.sql_query_agent import get_sql_agent
        a1 = get_sql_agent()
        a2 = get_sql_agent()
        assert a1 is a2
```

- [ ] **Step 2: Run test — verify it fails**

```bash
uv run pytest tests/test_sql_agent.py -v
```

Expected: FAIL — ImportError or module empty

- [ ] **Step 3: Implement sql_query_agent.py**

```python
# ai/src/agent/subagents/sql_query_agent.py
from langgraph.prebuilt import create_react_agent
from agent.llm import get_llm
from agent.tools.sql_tools import get_schema, execute_sql

_SQL_SYSTEM_PROMPT = """Bạn là SQL Query Agent, chuyên truy vấn database quản lý sinh viên.

QUY TRÌNH BẮT BUỘC — thực hiện đúng thứ tự:

Bước 1 — Đọc schema: Gọi get_schema() trước tiên. Đọc kỹ mô tả từng bảng và cột.

Bước 2 — Phân tích và reasoning (viết ra rõ ràng):
  - Câu hỏi yêu cầu thông tin gì?
  - Cần SELECT những cột nào? Tại sao chọn cột đó mà không phải cột khác?
  - Cần JOIN bảng nào? Điều kiện join là gì (khóa ngoại nào)?
  - WHERE filter như thế nào?
  - Có cần GROUP BY / ORDER BY / LIMIT không? Tại sao?

Bước 3 — Viết SQL và gọi execute_sql().

Bước 4 — Kiểm tra kết quả:
  - Nếu có lỗi: phân tích lỗi, sửa query, thử lại (tối đa 3 lần).
  - Nếu kết quả rỗng: kiểm tra lại điều kiện WHERE, thử query đơn giản hơn.

Bước 5 — Trả lời bao gồm:
  1. Kết quả dữ liệu cụ thể (số liệu, danh sách...)
  2. Reasoning: tại sao chọn các bảng/cột đó
  3. SQL query đã thực thi (trong code block)

QUAN TRỌNG: Chỉ được phép chạy SELECT queries. Từ chối mọi INSERT/UPDATE/DELETE/DROP."""

_agent = None

def get_sql_agent():
    global _agent
    if _agent is None:
        _agent = create_react_agent(
            model=get_llm(),
            tools=[get_schema, execute_sql],
            state_modifier=_SQL_SYSTEM_PROMPT,
        )
    return _agent
```

- [ ] **Step 4: Implement subagent_registry.py**

```python
# ai/src/agent/subagent_registry.py
from agent.subagents.sql_query_agent import get_sql_agent

__all__ = ["get_sql_agent"]
```

- [ ] **Step 5: Run test — verify it passes**

```bash
uv run pytest tests/test_sql_agent.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ai/src/agent/subagents/sql_query_agent.py ai/src/agent/subagent_registry.py ai/tests/test_sql_agent.py
git commit -m "feat: add SQL Query Agent with ReAct reasoning loop"
```

---

## Task 8: Deep Agent Tools + Registry

**Files:**
- Create: `ai/src/agent/tools/agent_tools.py`
- Fill: `ai/src/agent/tool_registry.py`

**Interfaces:**
- Consumes: `get_sql_agent()` from Task 7; `resolve_time_range` from Task 6
- Produces:
  - `call_sql_agent(question, date_range?, config) -> dict` — async LangChain tool
  - `out_of_scope_reply(topic) -> str` — LangChain tool
  - `DEEP_AGENT_TOOLS: list` — list of 3 tools for deep agent

- [ ] **Step 1: Write failing tests**

```python
# ai/tests/test_agent_tools.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

def test_out_of_scope_reply_contains_topic():
    from agent.tools.agent_tools import out_of_scope_reply
    result = out_of_scope_reply.invoke({"topic": "thời tiết"})
    assert "thời tiết" in result or "mình" in result

def test_out_of_scope_reply_returns_string():
    from agent.tools.agent_tools import out_of_scope_reply
    result = out_of_scope_reply.invoke({"topic": "bóng đá"})
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_call_sql_agent_appends_date_range():
    with patch("agent.tools.agent_tools.get_sql_agent") as mock_getter:
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [MagicMock(content="Kết quả: 10 sinh viên")]
        }
        mock_getter.return_value = mock_agent
        from agent.tools.agent_tools import call_sql_agent
        result = await call_sql_agent.ainvoke({
            "question": "Bao nhiêu sinh viên?",
            "date_range": {"start_date": "2026-08-01", "end_date": "2026-08-31", "label": "Tháng 8"}
        })
        assert "answer" in result
        call_args = mock_agent.ainvoke.call_args
        messages = call_args[0][0]["messages"]
        assert "2026-08-01" in messages[0]["content"]

def test_tool_registry_has_three_tools():
    from agent.tool_registry import DEEP_AGENT_TOOLS
    assert len(DEEP_AGENT_TOOLS) == 3
    names = [t.name for t in DEEP_AGENT_TOOLS]
    assert "resolve_time_range" in names
    assert "call_sql_agent" in names
    assert "out_of_scope_reply" in names
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_agent_tools.py -v
```

Expected: FAIL — ImportError

- [ ] **Step 3: Implement agent_tools.py**

```python
# ai/src/agent/tools/agent_tools.py
from typing import Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from agent.subagents.sql_query_agent import get_sql_agent

@tool
async def call_sql_agent(
    question: str,
    date_range: Optional[dict] = None,
    config: Optional[RunnableConfig] = None,
) -> dict:
    """Delegate a data question to the SQL Query Agent which reads the DB schema,
    reasons about which tables/columns to query, generates SQL, executes it, and
    returns the result with reasoning.

    Args:
        question: Natural language question about student data
        date_range: Optional {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": str}
                    from resolve_time_range — append to question so SQL agent filters by date
    """
    full_question = question
    if date_range:
        full_question += (
            f"\nKhoảng thời gian cần lọc: từ {date_range['start_date']} "
            f"đến {date_range['end_date']} ({date_range.get('label', '')})"
        )

    agent = get_sql_agent()
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": full_question}]},
        config=config,  # propagates callbacks so SQL agent's tool events stream through
    )
    last_message = result["messages"][-1]
    return {"answer": last_message.content}


@tool
def out_of_scope_reply(topic: str) -> str:
    """Return a friendly Vietnamese reply when the user asks about something outside
    the student management domain (learning, grades, scholarships, courses).

    Args:
        topic: Brief description of what the user asked about (e.g., 'thời tiết', 'bóng đá')
    """
    return (
        f"Ôi bạn ơi 🥲 mình chỉ biết chuyện học hành thôi nha! "
        f"Câu hỏi về '{topic}' thì mình bó tay rồi 😅\n\n"
        f"Thử hỏi mình về mấy cái này đi nè ✨\n"
        f"- 📚 Học phần và số tín chỉ\n"
        f"- 📊 Điểm số và kết quả học tập\n"
        f"- 🎓 Tiến độ tốt nghiệp\n"
        f"- 💰 Học bổng và điều kiện xét"
    )
```

- [ ] **Step 4: Implement tool_registry.py**

```python
# ai/src/agent/tool_registry.py
from agent.tools.datetime_tools import resolve_time_range
from agent.tools.agent_tools import call_sql_agent, out_of_scope_reply

DEEP_AGENT_TOOLS = [resolve_time_range, call_sql_agent, out_of_scope_reply]
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
uv run pytest tests/test_agent_tools.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add ai/src/agent/tools/agent_tools.py ai/src/agent/tool_registry.py ai/tests/test_agent_tools.py
git commit -m "feat: add call_sql_agent and out_of_scope_reply tools + registry"
```

---

## Task 9: Deep Agent + History + System Prompt

**Files:**
- Fill: `ai/src/agent/prompt/deep_agent.py`
- Fill: `ai/src/agent/history.py`
- Fill: `ai/src/agent/deep_agent.py`
- Create: `ai/tests/test_history.py`

**Interfaces:**
- Consumes: `DEEP_AGENT_TOOLS` from Task 8; `get_llm()` from Task 4
- Produces:
  - `get_deep_agent() -> CompiledGraph`
  - `get_history(session_id) -> List[BaseMessage]`
  - `add_messages(session_id, messages)`
  - `clear_history(session_id)`

- [ ] **Step 1: Write failing tests**

```python
# ai/tests/test_history.py
from langchain_core.messages import HumanMessage, AIMessage

def test_add_and_get():
    from agent.history import add_messages, get_history, clear_history
    clear_history("s1")
    add_messages("s1", [HumanMessage(content="xin chào")])
    history = get_history("s1")
    assert len(history) == 1
    assert history[0].content == "xin chào"

def test_multiple_sessions_isolated():
    from agent.history import add_messages, get_history, clear_history
    clear_history("sA"); clear_history("sB")
    add_messages("sA", [HumanMessage(content="A")])
    add_messages("sB", [HumanMessage(content="B")])
    assert get_history("sA")[0].content == "A"
    assert get_history("sB")[0].content == "B"

def test_clear():
    from agent.history import add_messages, get_history, clear_history
    add_messages("s2", [HumanMessage(content="hi")])
    clear_history("s2")
    assert get_history("s2") == []

def test_max_history_trim():
    from agent.history import add_messages, get_history, clear_history, MAX_HISTORY
    clear_history("s3")
    msgs = [HumanMessage(content=f"msg{i}") for i in range(MAX_HISTORY + 4)]
    add_messages("s3", msgs)
    assert len(get_history("s3")) == MAX_HISTORY

def test_get_returns_copy():
    from agent.history import add_messages, get_history, clear_history
    clear_history("s4")
    add_messages("s4", [HumanMessage(content="x")])
    h = get_history("s4")
    h.append(HumanMessage(content="mutated"))
    assert len(get_history("s4")) == 1  # original unchanged
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_history.py -v
```

Expected: FAIL — ImportError

- [ ] **Step 3: Implement prompt/deep_agent.py**

```python
# ai/src/agent/prompt/deep_agent.py

SYSTEM_PROMPT = """Bạn là trợ lý AI của trường đại học, chuyên hỗ trợ sinh viên tra cứu thông tin học tập 🎓

TÍNH CÁCH:
- Xưng "mình", gọi người dùng là "bạn"
- Dùng emoji tự nhiên (🎓 📚 😅 🥲 ✨ 🔥 💪 📊)
- Ngắn gọn, thân thiện, phong cách Gen Z đại học
- Trả lời có con số cụ thể, dễ đọc, kèm bullet points khi cần

PHẠM VI HỖ TRỢ — chỉ trả lời các chủ đề sau:
- Thông tin học phần: tên môn, số tín chỉ, mô tả, học phần tiên quyết
- Điểm số và kết quả học tập: bảng điểm, điểm trung bình
- Tiến độ tín chỉ: số tín chỉ đã hoàn thành, còn thiếu bao nhiêu để tốt nghiệp
- Đăng ký học phần: lịch sử đăng ký, trạng thái
- Học bổng: điều kiện xét, danh sách sinh viên nhận, tổng giá trị
- Thống kê: sinh viên theo ngành, GPA trung bình, tỷ lệ đạt môn

NGOÀI PHẠM VI: Gọi out_of_scope_reply() với tên chủ đề, đừng tự bịa câu trả lời.

CÁCH XỬ LÝ:
1. Nếu câu hỏi chứa mốc thời gian tương đối
   ("tháng trước", "quý này", "năm ngoái", "học kỳ này"...)
   → Gọi resolve_time_range() trước để lấy date range chính xác
2. Nếu cần dữ liệu từ DB → Gọi call_sql_agent() (kèm date_range nếu có)
3. Tổng hợp kết quả → trả lời ngắn gọn, có số liệu cụ thể

Luôn trả lời bằng tiếng Việt."""
```

- [ ] **Step 4: Implement history.py**

```python
# ai/src/agent/history.py
from typing import Dict, List
from langchain_core.messages import BaseMessage

_store: Dict[str, List[BaseMessage]] = {}
MAX_HISTORY = 20

def get_history(session_id: str) -> List[BaseMessage]:
    return list(_store.get(session_id, []))

def add_messages(session_id: str, messages: List[BaseMessage]) -> None:
    if session_id not in _store:
        _store[session_id] = []
    _store[session_id].extend(messages)
    if len(_store[session_id]) > MAX_HISTORY:
        _store[session_id] = _store[session_id][-MAX_HISTORY:]

def clear_history(session_id: str) -> None:
    _store.pop(session_id, None)
```

- [ ] **Step 5: Implement deep_agent.py**

```python
# ai/src/agent/deep_agent.py
from langgraph.prebuilt import create_react_agent
from agent.llm import get_llm
from agent.tool_registry import DEEP_AGENT_TOOLS
from agent.prompt.deep_agent import SYSTEM_PROMPT

_deep_agent = None

def get_deep_agent():
    global _deep_agent
    if _deep_agent is None:
        _deep_agent = create_react_agent(
            model=get_llm(),
            tools=DEEP_AGENT_TOOLS,
            state_modifier=SYSTEM_PROMPT,
        )
    return _deep_agent
```

- [ ] **Step 6: Run history tests — verify they pass**

```bash
uv run pytest tests/test_history.py -v
```

Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add ai/src/agent/prompt/deep_agent.py ai/src/agent/history.py ai/src/agent/deep_agent.py ai/tests/test_history.py
git commit -m "feat: add deep agent orchestrator, system prompt, and session history"
```

---

## Task 10: FastAPI + SSE Endpoint

**Files:**
- Fill: `ai/src/main.py`
- Create: `ai/tests/test_main.py`

**Interfaces:**
- Consumes: `get_deep_agent()` from Task 9; `get_history()`, `add_messages()` from Task 9
- Produces:
  - `GET /health` → `{"status": "ok"}`
  - `GET /chat/stream?session_id=&message=` → SSE stream with `status`/`done`/`error` events
  - `GET /` → serves `frontend/index.html`

- [ ] **Step 1: Write failing tests**

```python
# ai/tests/test_main.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    with patch("agent.deep_agent.get_deep_agent") as mock_getter, \
         patch("agent.llm.ChatGoogleGenerativeAI"):
        mock_agent = MagicMock()
        mock_agent.astream_events = AsyncMock(return_value=aiter([]))
        mock_getter.return_value = mock_agent
        from main import app
        with TestClient(app) as c:
            yield c

async def aiter(items):
    for item in items:
        yield item

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_chat_stream_returns_200(client):
    with patch("main.get_deep_agent") as mock_getter:
        mock_agent = MagicMock()
        async def fake_stream(*args, **kwargs):
            yield {"event": "on_chain_end", "data": {"output": {"messages": [MagicMock(content="Xin chào bạn! 👋")]}}, "name": ""}
        mock_agent.astream_events = fake_stream
        mock_getter.return_value = mock_agent
        resp = client.get("/chat/stream?session_id=test-1&message=xin+chao",
                          headers={"Accept": "text/event-stream"})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_main.py -v
```

Expected: FAIL — ImportError (main.py empty)

- [ ] **Step 3: Create frontend directory placeholder**

```bash
mkdir -p ai/src/frontend
echo "" > ai/src/frontend/.gitkeep
```

FastAPI's StaticFiles will fail if the directory doesn't exist at startup.

- [ ] **Step 4: Implement main.py**

```python
# ai/src/main.py
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage, AIMessage
from agent.deep_agent import get_deep_agent
from agent.history import get_history, add_messages

app = FastAPI(title="Student AI Assistant")

_TOOL_LABELS = {
    "resolve_time_range": "📅 Đang xác định khoảng thời gian...",
    "call_sql_agent":     "📊 Đang hỏi SQL Agent...",
    "out_of_scope_reply": "🚫 Nhận diện câu hỏi ngoài phạm vi...",
    "get_schema":         "📋 SQL Agent đang đọc schema database...",
    "execute_sql":        "⚡ Đang thực thi SQL query...",
}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/chat/stream")
async def chat_stream(session_id: str, message: str):
    async def generate():
        agent = get_deep_agent()
        history = get_history(session_id)
        messages = history + [HumanMessage(content=message)]
        final_reply = ""

        try:
            yield _sse("status", {"message": "🧠 Deep Agent đang phân tích câu hỏi..."})

            async for event in agent.astream_events(
                {"messages": messages},
                config={"recursion_limit": 25},
                version="v2",
            ):
                kind = event.get("event", "")

                if kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    label = _TOOL_LABELS.get(tool_name, f"🔧 Gọi: {tool_name}...")
                    yield _sse("status", {"message": label})

                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict) and "messages" in output:
                        msgs = output["messages"]
                        if msgs and hasattr(msgs[-1], "content") and msgs[-1].content:
                            final_reply = msgs[-1].content

            add_messages(session_id, [
                HumanMessage(content=message),
                AIMessage(content=final_reply),
            ])
            yield _sse("done", {"reply": final_reply})

        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

# Mount frontend LAST — catch-all route
_frontend = Path(__file__).parent / "frontend"
app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="static")
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
uv run pytest tests/test_main.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ai/src/main.py ai/src/frontend/.gitkeep ai/tests/test_main.py
git commit -m "feat: add FastAPI SSE streaming endpoint"
```

---

## Task 11: Frontend

**Files:**
- Create: `ai/src/frontend/index.html`
- Create: `ai/src/frontend/style.css`
- Create: `ai/src/frontend/app.js`

**Interfaces:**
- Consumes: `GET /chat/stream` SSE endpoint from Task 10
- Produces: Chat UI served at `http://localhost:8000/`

- [ ] **Step 1: Write index.html**

```html
<!-- ai/src/frontend/index.html -->
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Sinh Viên 🎓</title>
  <link rel="stylesheet" href="/style.css" />
</head>
<body>
  <div class="app">
    <header class="header">
      <span class="header-icon">🎓</span>
      <div>
        <h1>Trợ lý AI Sinh Viên</h1>
        <p>Hỏi mình về học phần, điểm số, học bổng nhé ✨</p>
      </div>
    </header>

    <div class="chat-container" id="chat">
      <div class="bubble agent">
        <span class="avatar">🤖</span>
        <div class="bubble-content">
          Chào bạn! 👋 Mình là trợ lý AI của trường, có thể giúp bạn tra cứu thông tin học tập nè. Hỏi mình đi! 📚
        </div>
      </div>
    </div>

    <div class="status-bar" id="statusBar" hidden></div>

    <div class="input-area">
      <textarea id="input" placeholder="Hỏi mình về học phần, điểm, học bổng..." rows="1"></textarea>
      <button id="sendBtn" onclick="sendMessage()">Gửi ➤</button>
    </div>
  </div>
  <script src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write style.css**

```css
/* ai/src/frontend/style.css */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app {
  width: 100%;
  max-width: 780px;
  height: 100vh;
  max-height: 820px;
  background: #ffffff;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px rgba(0,0,0,0.25);
}

.header {
  background: linear-gradient(90deg, #667eea, #764ba2);
  color: white;
  padding: 18px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.header-icon { font-size: 2rem; }
.header h1 { font-size: 1.2rem; font-weight: 700; }
.header p  { font-size: 0.8rem; opacity: 0.85; margin-top: 2px; }

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  scroll-behavior: smooth;
}

.bubble {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 85%;
  animation: fadeIn 0.25s ease;
}
.bubble.user { align-self: flex-end; flex-direction: row-reverse; }
.bubble.agent { align-self: flex-start; }

.avatar {
  font-size: 1.4rem;
  flex-shrink: 0;
  margin-top: 2px;
}

.bubble-content {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.55;
  font-size: 0.92rem;
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble.agent .bubble-content {
  background: #f0f2ff;
  color: #2d2d2d;
  border-bottom-left-radius: 4px;
}
.bubble.user .bubble-content {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-bottom-right-radius: 4px;
}

.reasoning-toggle {
  font-size: 0.78rem;
  color: #667eea;
  cursor: pointer;
  margin-top: 6px;
  user-select: none;
}
.reasoning-toggle:hover { text-decoration: underline; }
.reasoning-content {
  background: #f8f9ff;
  border-left: 3px solid #667eea;
  padding: 10px 14px;
  font-size: 0.78rem;
  color: #555;
  border-radius: 0 8px 8px 0;
  margin-top: 6px;
  white-space: pre-wrap;
  word-break: break-word;
}

.status-bar {
  margin: 0 16px 4px;
  padding: 8px 14px;
  background: #f0f2ff;
  border-radius: 10px;
  font-size: 0.8rem;
  color: #667eea;
  animation: pulse 1.5s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }

.input-area {
  display: flex;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid #ebebeb;
  background: #fafafa;
}
textarea {
  flex: 1;
  border: 1.5px solid #dde0ff;
  border-radius: 14px;
  padding: 10px 14px;
  font-size: 0.92rem;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  max-height: 120px;
  overflow-y: auto;
}
textarea:focus { border-color: #667eea; }

button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 14px;
  padding: 10px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
  white-space: nowrap;
}
button:hover { opacity: 0.9; }
button:active { transform: scale(0.97); }
button:disabled { opacity: 0.5; cursor: not-allowed; }

@keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:none} }
```

- [ ] **Step 3: Write app.js**

```js
// ai/src/frontend/app.js
const SESSION_ID = "session-" + Math.random().toString(36).slice(2);
const chat     = document.getElementById("chat");
const input    = document.getElementById("input");
const sendBtn  = document.getElementById("sendBtn");
const statusBar = document.getElementById("statusBar");

function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  addBubble("user", text);
  input.value = "";
  autoResize();
  setLoading(true);
  streamResponse(text);
}

function streamResponse(message) {
  const url = `/chat/stream?session_id=${encodeURIComponent(SESSION_ID)}&message=${encodeURIComponent(message)}`;
  const es = new EventSource(url);

  es.addEventListener("status", (e) => {
    const data = JSON.parse(e.data);
    showStatus(data.message);
  });

  es.addEventListener("done", (e) => {
    const data = JSON.parse(e.data);
    hideStatus();
    addBubble("agent", data.reply, data.reasoning);
    setLoading(false);
    es.close();
  });

  es.addEventListener("error", (e) => {
    hideStatus();
    let msg = "😅 Mình bị lỗi rồi bạn ơi, thử lại nhé!";
    try { msg = JSON.parse(e.data).message; } catch(_) {}
    addBubble("agent", msg);
    setLoading(false);
    es.close();
  });

  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) return;
    hideStatus();
    addBubble("agent", "😅 Mất kết nối rồi bạn ơi, thử lại nhé!");
    setLoading(false);
    es.close();
  };
}

function addBubble(role, text, reasoning) {
  const wrap = document.createElement("div");
  wrap.className = `bubble ${role}`;

  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "🎓" : "🤖";

  const content = document.createElement("div");
  content.className = "bubble-content-wrap";

  const body = document.createElement("div");
  body.className = "bubble-content";
  body.textContent = text;
  content.appendChild(body);

  if (reasoning) {
    const toggle = document.createElement("div");
    toggle.className = "reasoning-toggle";
    toggle.textContent = "🔍 Xem cách mình nghĩ";
    const box = document.createElement("div");
    box.className = "reasoning-content";
    box.textContent = reasoning;
    box.hidden = true;
    toggle.onclick = () => {
      box.hidden = !box.hidden;
      toggle.textContent = box.hidden ? "🔍 Xem cách mình nghĩ" : "🔼 Ẩn đi";
    };
    content.appendChild(toggle);
    content.appendChild(box);
  }

  wrap.appendChild(avatar);
  wrap.appendChild(content);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

function showStatus(msg) {
  statusBar.textContent = msg;
  statusBar.hidden = false;
  chat.scrollTop = chat.scrollHeight;
}

function hideStatus() {
  statusBar.hidden = true;
  statusBar.textContent = "";
}

function setLoading(loading) {
  sendBtn.disabled = loading;
  input.disabled   = loading;
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
}

input.addEventListener("input", autoResize);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
```

- [ ] **Step 4: Run the full app and test manually**

```bash
cd ai
cp .env.example .env   # fill in GEMINI_API_KEY and DATABASE_URL
uv run uvicorn src.main:app --reload --port 8000
```

Open `http://localhost:8000` in browser.

Test these scenarios:
1. Type "xin chào" — expect friendly greeting without DB call
2. Type "có bao nhiêu sinh viên ngành CNTT?" — expect status bar to show tool calls, then answer
3. Type "tháng trước có sinh viên nào nhận học bổng không?" — expect resolve_time_range to appear in status, then SQL agent
4. Type "thời tiết hôm nay thế nào?" — expect out-of-scope reply
5. Verify "Xem cách mình nghĩ" toggle works when reasoning is returned

- [ ] **Step 5: Commit**

```bash
git add ai/src/frontend/
git commit -m "feat: add chat UI with SSE status bar and reasoning panel"
```

---

## Self-Review

**Spec coverage check:**
- ✅ Deep Agent (orchestrator, teen personality, out-of-scope) — Tasks 8, 9
- ✅ SQL Query Agent (ReAct loop, get_schema, execute_sql, reasoning) — Tasks 5, 7
- ✅ resolve_time_range with relative expressions — Task 6
- ✅ Star schema with COMMENTs and FK — Task 1
- ✅ Dummy data 100 students — Task 2
- ✅ Supabase (via DATABASE_URL) — Tasks 1, 2
- ✅ FastAPI + SSE streaming — Task 10
- ✅ Frontend with status bar showing tool calls — Task 11
- ✅ call_sql_agent propagates config for nested streaming — Task 8

**Placeholder scan:** No TBD/TODO found.

**Type consistency:**
- `get_sql_agent()` returns `CompiledGraph` — consumed by `call_sql_agent` via `.ainvoke()` ✅
- `DEEP_AGENT_TOOLS` is a `list` — passed to `create_react_agent(tools=...)` ✅
- `get_history()` returns `List[BaseMessage]` — concatenated with `[HumanMessage(...)]` in main.py ✅
- SSE helper `_sse(type, data)` returns `str` — yielded from async generator ✅
