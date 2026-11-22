"""Initialize and seed local SQLite database (fe_be/student.db) using the exact
schema from fe_be/schema.sql and deterministic seed logic from fe_be/seed.py.
Also stores all table and column COMMENT ON metadata from schema.sql so
get_schema() returns the exact same annotated schema representation.
"""
import datetime
import random
import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "student.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

import seed as pg_seed


def build_sqlite_db() -> dict:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # 1. Parse COMMENT ON TABLE and COMMENT ON COLUMN from schema.sql
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    table_comments: dict[str, str] = {}
    column_comments: dict[tuple[str, str], str] = {}

    for m in re.finditer(r"COMMENT\s+ON\s+TABLE\s+(\w+)\s+IS\s+'([^']*)';", schema_text, re.I):
        table_comments[m.group(1).lower()] = m.group(2)

    for m in re.finditer(r"COMMENT\s+ON\s+COLUMN\s+(\w+)\.(\w+)\s+IS\s+'([^']*)';", schema_text, re.I):
        column_comments[(m.group(1).lower(), m.group(2).lower())] = m.group(3)

    # 2. Create metadata tables for comments
    cur.execute("""
        CREATE TABLE _meta_table_comments (
            table_name TEXT PRIMARY KEY,
            table_comment TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE _meta_column_comments (
            table_name TEXT,
            column_name TEXT,
            column_comment TEXT,
            PRIMARY KEY (table_name, column_name)
        );
    """)
    for t_name, cmt in table_comments.items():
        cur.execute("INSERT INTO _meta_table_comments VALUES (?, ?)", (t_name, cmt))
    for (t_name, c_name), cmt in column_comments.items():
        cur.execute("INSERT INTO _meta_column_comments VALUES (?, ?, ?)", (t_name, c_name, cmt))

    # 3. Create the 8 Star Schema tables in SQLite compatible DDL
    cur.executescript("""
    CREATE TABLE dim_major (
        major_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        major_code VARCHAR(10)  UNIQUE NOT NULL,
        major_name VARCHAR(100) NOT NULL,
        faculty    VARCHAR(100) NOT NULL,
        total_credits_required INT NOT NULL DEFAULT 120,
        duration_years         INT NOT NULL DEFAULT 4
    );

    CREATE TABLE dim_department (
        department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        department_code VARCHAR(10)  UNIQUE NOT NULL,
        department_name VARCHAR(100) NOT NULL,
        faculty         VARCHAR(100),
        head_name       VARCHAR(100)
    );

    CREATE TABLE dim_semester (
        semester_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        semester_code   VARCHAR(20)  UNIQUE NOT NULL,
        semester_name   VARCHAR(100) NOT NULL,
        academic_year   VARCHAR(10)  NOT NULL,
        semester_number INT NOT NULL CHECK (semester_number IN (1, 2, 3)),
        start_date      DATE NOT NULL,
        end_date        DATE NOT NULL,
        is_current      BOOLEAN NOT NULL DEFAULT 0
    );

    CREATE TABLE dim_student (
        student_id              INTEGER PRIMARY KEY AUTOINCREMENT,
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

    CREATE TABLE dim_course (
        course_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code   VARCHAR(10)  UNIQUE NOT NULL,
        course_name   VARCHAR(200) NOT NULL,
        credits       INT NOT NULL CHECK (credits BETWEEN 1 AND 4),
        department_id INT NOT NULL REFERENCES dim_department(department_id),
        description   TEXT,
        is_required   BOOLEAN NOT NULL DEFAULT 1,
        prerequisites VARCHAR(200)
    );

    CREATE TABLE dim_scholarship (
        scholarship_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        scholarship_code VARCHAR(20)  UNIQUE NOT NULL,
        scholarship_name VARCHAR(200) NOT NULL,
        scholarship_type VARCHAR(50)  NOT NULL CHECK (scholarship_type IN ('merit', 'need', 'enterprise')),
        amount           NUMERIC(12,2) NOT NULL,
        min_gpa          NUMERIC(3,2),
        description      TEXT
    );

    CREATE TABLE fact_enrollment (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id    INT NOT NULL REFERENCES dim_student(student_id),
        course_id     INT NOT NULL REFERENCES dim_course(course_id),
        semester_id   INT NOT NULL REFERENCES dim_semester(semester_id),
        grade         NUMERIC(4,2),
        grade_letter  VARCHAR(2),
        credits_earned INT NOT NULL DEFAULT 0,
        status        VARCHAR(20) NOT NULL DEFAULT 'in_progress'
                          CHECK (status IN ('passed', 'failed', 'in_progress', 'withdrawn')),
        registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (student_id, course_id, semester_id)
    );

    CREATE TABLE fact_scholarship_award (
        award_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id     INT NOT NULL REFERENCES dim_student(student_id),
        scholarship_id INT NOT NULL REFERENCES dim_scholarship(scholarship_id),
        semester_id    INT NOT NULL REFERENCES dim_semester(semester_id),
        amount_awarded NUMERIC(12,2) NOT NULL,
        awarded_at     DATE NOT NULL DEFAULT CURRENT_DATE,
        UNIQUE (student_id, scholarship_id, semester_id)
    );
    """)

    # 4. Seed with exact deterministic seed from seed.py (random.seed(42), Faker("vi_VN"))
    fake = Faker("vi_VN")
    Faker.seed(42)
    random.seed(42)

    cur.executemany(
        "INSERT OR IGNORE INTO dim_department (department_code, department_name, faculty, head_name) VALUES (?, ?, ?, ?)",
        pg_seed.DEPARTMENTS,
    )
    cur.executemany(
        "INSERT OR IGNORE INTO dim_major (major_code, major_name, faculty, total_credits_required, duration_years) VALUES (?, ?, ?, ?, ?)",
        pg_seed.MAJORS,
    )
    cur.executemany(
        "INSERT OR IGNORE INTO dim_semester (semester_code, semester_name, academic_year, semester_number, start_date, end_date, is_current) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(c, n, ay, sn, sd.isoformat(), ed.isoformat(), int(ic)) for c, n, ay, sn, sd, ed, ic in pg_seed.SEMESTERS],
    )

    cur.execute("SELECT department_code, department_id FROM dim_department")
    dept_map = {code: dept_id for code, dept_id in cur.fetchall()}
    course_rows = [
        (code, name, credits, dept_map[dept_code], desc, int(is_req), prereq)
        for code, name, credits, dept_code, desc, is_req, prereq in pg_seed.COURSES
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO dim_course (course_code, course_name, credits, department_id, description, is_required, prerequisites) VALUES (?, ?, ?, ?, ?, ?, ?)",
        course_rows,
    )

    cur.executemany(
        "INSERT OR IGNORE INTO dim_scholarship (scholarship_code, scholarship_name, scholarship_type, amount, min_gpa, description) VALUES (?, ?, ?, ?, ?, ?)",
        pg_seed.SCHOLARSHIPS,
    )

    # Students
    cur.execute("SELECT major_id FROM dim_major")
    major_ids = [row[0] for row in cur.fetchall()]
    year_counter = {year: 1 for year in pg_seed.ADMISSION_YEARS}
    student_rows = []
    for _ in range(pg_seed.STUDENT_COUNT):
        admission_year = random.choices(pg_seed.ADMISSION_YEARS, weights=pg_seed.YEAR_WEIGHTS)[0]
        student_code = f"SV{admission_year}{year_counter[admission_year]:03d}"
        year_counter[admission_year] += 1
        gender = random.choice(["male", "female"])
        dob = fake.date_of_birth(minimum_age=18, maximum_age=24).isoformat()
        current_gpa = round(random.uniform(1.0, 4.0), 2)
        total_credits_completed = random.randint(0, 90)
        status = random.choices(pg_seed.STUDENT_STATUS_OPTIONS, weights=pg_seed.STUDENT_STATUS_WEIGHTS)[0]
        student_rows.append((
            student_code,
            fake.name(),
            gender,
            dob,
            f"{student_code.lower()}@student.edu.vn",
            fake.phone_number()[:15],
            random.choice(major_ids),
            admission_year,
            current_gpa,
            total_credits_completed,
            status,
        ))
    cur.executemany(
        "INSERT OR IGNORE INTO dim_student (student_code, full_name, gender, date_of_birth, email, phone, major_id, admission_year, current_gpa, total_credits_completed, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        student_rows,
    )

    # Enrollments
    cur.execute("SELECT student_id FROM dim_student")
    student_ids = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT semester_id, is_current FROM dim_semester ORDER BY start_date")
    semesters = cur.fetchall()
    cur.execute("SELECT course_id, credits FROM dim_course")
    all_courses = cur.fetchall()

    enrollment_rows = []
    for student_id in student_ids:
        student_course_pool = random.sample(
            all_courses,
            min(len(all_courses), random.randint(pg_seed.COURSES_PER_STUDENT_MIN, pg_seed.COURSES_PER_STUDENT_MAX)),
        )
        for semester_id, is_current_semester in semesters:
            sem_courses = random.sample(
                student_course_pool,
                min(len(student_course_pool), random.randint(pg_seed.ENROLLMENTS_PER_SEM_MIN, pg_seed.ENROLLMENTS_PER_SEM_MAX)),
            )
            for course_id, course_credits in sem_courses:
                enrollment_rows.append(
                    pg_seed._build_enrollment_row(
                        student_id, course_id, semester_id, course_credits, bool(is_current_semester)
                    )
                )
    cur.executemany(
        "INSERT OR IGNORE INTO fact_enrollment (student_id, course_id, semester_id, grade, grade_letter, credits_earned, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        enrollment_rows,
    )

    # Scholarship awards (exact order from seed.py lines 365-367: before UPDATE dim_student)
    cur.execute("SELECT student_id, current_gpa FROM dim_student WHERE status = 'active'")
    active_students = cur.fetchall()
    cur.execute("SELECT scholarship_id, min_gpa, amount FROM dim_scholarship")
    scholarships = cur.fetchall()
    cur.execute(
        "SELECT semester_id, start_date, end_date FROM dim_semester"
        " WHERE is_current = 0 ORDER BY start_date DESC LIMIT 2"
    )
    past_semesters = [
        (row[0], date.fromisoformat(row[1]), date.fromisoformat(row[2]))
        for row in cur.fetchall()
    ]

    award_rows = []
    for student_id, student_gpa in active_students:
        for scholarship_id, min_gpa, scholarship_amount in scholarships:
            gpa_qualifies = min_gpa is None or float(student_gpa) >= float(min_gpa)
            if not gpa_qualifies:
                continue
            if random.random() >= pg_seed.SCHOLARSHIP_AWARD_PROBABILITY:
                continue
            sem_id, sem_start, sem_end = random.choice(past_semesters)
            awarded_at = (sem_start + timedelta(days=random.randint(0, (sem_end - sem_start).days))).isoformat()
            award_rows.append((student_id, scholarship_id, sem_id, float(scholarship_amount), awarded_at))

    cur.executemany(
        "INSERT OR IGNORE INTO fact_scholarship_award (student_id, scholarship_id, semester_id, amount_awarded, awarded_at) VALUES (?, ?, ?, ?, ?)",
        award_rows,
    )

    # Update student GPA and total credits completed based on fact_enrollment (just like seed.py lines 367-380)
    cur.execute("""
        UPDATE dim_student
        SET total_credits_completed = COALESCE((
                SELECT SUM(credits_earned)
                FROM fact_enrollment
                WHERE fact_enrollment.student_id = dim_student.student_id
                  AND status IN ('passed', 'failed')
            ), 0),
            current_gpa = COALESCE((
                SELECT ROUND(AVG(grade) / 2.5, 2)
                FROM fact_enrollment
                WHERE fact_enrollment.student_id = dim_student.student_id
                  AND status IN ('passed', 'failed')
            ), 0.00)
        WHERE EXISTS (
            SELECT 1 FROM fact_enrollment
            WHERE fact_enrollment.student_id = dim_student.student_id
              AND status IN ('passed', 'failed')
        )
    """)

    conn.commit()
    conn.close()
    return {}


if __name__ == "__main__":
    build_sqlite_db()
