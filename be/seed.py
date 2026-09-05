# be/seed.py
"""Seed script for the student management star schema.

Usage:
    uv run --with psycopg2-binary --with python-dotenv --with faker python seed.py

Reads DATABASE_URL from be/.env (or the environment).
Idempotent: uses ON CONFLICT DO NOTHING throughout.
"""

import logging
import os
import random
from datetime import date

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from faker import Faker

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

fake = Faker("vi_VN")
random.seed(42)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STUDENT_COUNT = 100
ADMISSION_YEARS = [2021, 2022, 2023, 2024]
YEAR_WEIGHTS = [25, 25, 25, 25]
STUDENT_STATUS_OPTIONS = ["active", "graduated", "suspended", "dropped"]
STUDENT_STATUS_WEIGHTS = [85, 8, 4, 3]
COURSES_PER_STUDENT_MIN = 4
COURSES_PER_STUDENT_MAX = 6
ENROLLMENTS_PER_SEM_MIN = 3
ENROLLMENTS_PER_SEM_MAX = 5
SCHOLARSHIP_AWARD_PROBABILITY = 0.30
PASSING_GRADE_THRESHOLD = 4.0

DEPARTMENTS = [
    ("CNTT",      "Khoa Công nghệ Thông tin",         "Kỹ thuật",        "TS. Nguyễn Văn An"),
    ("TOAN",      "Bộ môn Toán - Tin",                "Khoa học cơ bản", "TS. Trần Thị Bình"),
    ("NGOAINGU",  "Bộ môn Ngoại ngữ",                 "Khoa học xã hội", "ThS. Lê Văn Cường"),
    ("DAICUONG",  "Bộ môn Giáo dục Đại cương",        None,              "TS. Phạm Thị Dung"),
]

MAJORS = [
    ("CNTT",  "Công nghệ Thông tin",          "Kỹ thuật", 120, 4),
    ("KTPM",  "Kỹ thuật Phần mềm",            "Kỹ thuật", 125, 4),
    ("HTTT",  "Hệ thống Thông tin",            "Kỹ thuật", 120, 4),
    ("MMT",   "Mạng Máy tính & Truyền thông", "Kỹ thuật", 120, 4),
    ("KHMT",  "Khoa học Máy tính",             "Khoa học", 130, 4),
]

# (code, name, credits, dept_code, description, is_required, prerequisites)
# credits must be 1-4 per schema CHECK constraint
COURSES = [
    ("CS101",   "Nhập môn Lập trình",                   2, "CNTT",     "Các khái niệm cơ bản về lập trình, biến, vòng lặp, hàm với Python.",             True,  None),
    ("CS102",   "Cấu trúc Dữ liệu & Giải thuật",        3, "CNTT",     "Mảng, danh sách liên kết, cây, đồ thị và các thuật toán sắp xếp, tìm kiếm.",    True,  "CS101"),
    ("CS201",   "Lập trình Hướng đối tượng",             3, "CNTT",     "Các khái niệm OOP: class, kế thừa, đa hình, interface. Thực hành với Java.",    True,  "CS101"),
    ("CS202",   "Cơ sở Dữ liệu",                        3, "CNTT",     "Thiết kế CSDL quan hệ, SQL, chuẩn hóa, transaction.",                            True,  "CS101"),
    ("CS301",   "Công nghệ Web",                         3, "CNTT",     "HTML/CSS/JS, REST API, FastAPI, React cơ bản.",                                   True,  "CS201"),
    ("CS302",   "Học máy cơ bản",                        3, "CNTT",     "Hồi quy, phân loại, clustering, neural network cơ bản.",                         False, "CS102"),
    ("CS303",   "Mạng máy tính",                         3, "CNTT",     "Mô hình OSI/TCP-IP, giao thức mạng, bảo mật mạng cơ bản.",                      True,  None),
    ("CS401",   "Trí tuệ nhân tạo",                      3, "CNTT",     "Tìm kiếm, logic, học tăng cường, xử lý ngôn ngữ tự nhiên.",                     False, "CS302"),
    ("CS402",   "Kiến trúc phần mềm",                    3, "CNTT",     "Design patterns, microservices, DevOps cơ bản.",                                  False, "CS301"),
    ("CS403",   "Đồ án tốt nghiệp",                      4, "CNTT",     "Dự án nghiên cứu hoặc ứng dụng thực tế hoàn chỉnh.",                             True,  None),
    ("MATH101", "Giải tích 1",                           3, "TOAN",     "Giới hạn, đạo hàm, tích phân một biến.",                                         True,  None),
    ("MATH102", "Giải tích 2",                           3, "TOAN",     "Tích phân nhiều biến, chuỗi số, phương trình vi phân.",                          True,  "MATH101"),
    ("MATH201", "Đại số tuyến tính",                     3, "TOAN",     "Ma trận, định thức, không gian vectơ, trị riêng.",                               True,  None),
    ("MATH202", "Xác suất & Thống kê",                   3, "TOAN",     "Biến ngẫu nhiên, phân phối xác suất, kiểm định giả thuyết.",                    True,  "MATH101"),
    ("MATH301", "Toán rời rạc",                          3, "TOAN",     "Tổ hợp, đồ thị, logic, lý thuyết số.",                                           True,  None),
    ("MATH302", "Tối ưu hóa",                            2, "TOAN",     "Quy hoạch tuyến tính, gradient descent, thuật toán tối ưu.",                     False, "MATH201"),
    ("ENG101",  "Tiếng Anh cơ bản 1",                   2, "NGOAINGU", "Ngữ pháp và từ vựng tiếng Anh cơ bản, luyện nghe nói.",                          True,  None),
    ("ENG102",  "Tiếng Anh cơ bản 2",                   2, "NGOAINGU", "Tiếp nối ENG101, kỹ năng đọc viết.",                                             True,  "ENG101"),
    ("ENG201",  "Tiếng Anh chuyên ngành IT",             2, "NGOAINGU", "Từ vựng kỹ thuật, đọc tài liệu IT, viết email chuyên nghiệp.",                  True,  "ENG102"),
    ("GEN101",  "Triết học Mác - Lênin",                 3, "DAICUONG", "Chủ nghĩa duy vật biện chứng và lịch sử.",                                       True,  None),
    ("GEN102",  "Kinh tế chính trị Mác - Lênin",         2, "DAICUONG", "Lý luận kinh tế cơ bản theo quan điểm Mác.",                                     True,  None),
    ("GEN103",  "Tư tưởng Hồ Chí Minh",                  2, "DAICUONG", "Hệ thống tư tưởng của Hồ Chí Minh.",                                             True,  None),
    ("GEN104",  "Lịch sử Đảng Cộng sản Việt Nam",        2, "DAICUONG", "Lịch sử thành lập và phát triển của Đảng.",                                      True,  None),
    ("GEN105",  "Giáo dục thể chất 1",                   1, "DAICUONG", "Thể dục thể thao cơ bản, rèn luyện sức khỏe.",                                   True,  None),
    ("GEN106",  "Giáo dục thể chất 2",                   1, "DAICUONG", "Tiếp nối GEN105, các môn thể thao tự chọn.",                                     True,  "GEN105"),
    ("GEN107",  "Giáo dục quốc phòng - an ninh",         3, "DAICUONG", "Kiến thức quân sự và an ninh quốc gia.",                                         True,  None),
    ("CS501",   "Phát triển ứng dụng Mobile",            3, "CNTT",     "React Native, Android, iOS cơ bản.",                                             False, "CS301"),
    ("CS502",   "An toàn thông tin",                      3, "CNTT",     "Mã hóa, bảo mật web, kiểm thử xâm nhập cơ bản.",                               False, "CS303"),
    ("CS503",   "Điện toán đám mây",                      2, "CNTT",     "AWS/GCP/Azure cơ bản, containerization, CI/CD.",                                 False, "CS303"),
    ("CS504",   "Phân tích dữ liệu lớn",                  3, "CNTT",     "Hadoop, Spark, data pipeline, visualization.",                                   False, "CS302"),
]

# (code, name, academic_year, semester_number, start_date, end_date, is_current)
SEMESTERS = [
    ("HK1-2023-2024", "Học kỳ 1 năm học 2023-2024",  "2023-2024", 1, date(2023, 9, 4),  date(2024, 1, 14), False),
    ("HK2-2023-2024", "Học kỳ 2 năm học 2023-2024",  "2023-2024", 2, date(2024, 1, 22), date(2024, 5, 31), False),
    ("HK3-2023-2024", "Học kỳ hè năm học 2023-2024", "2023-2024", 3, date(2024, 6, 10), date(2024, 8, 16), False),
    ("HK1-2024-2025", "Học kỳ 1 năm học 2024-2025",  "2024-2025", 1, date(2024, 9, 2),  date(2025, 1, 12), False),
    ("HK2-2024-2025", "Học kỳ 2 năm học 2024-2025",  "2024-2025", 2, date(2025, 1, 20), date(2025, 5, 30), False),
    ("HK1-2025-2026", "Học kỳ 1 năm học 2025-2026",  "2025-2026", 1, date(2025, 9, 1),  date(2026, 1, 11), True),
]

SCHOLARSHIPS = [
    ("HB-KK1", "Học bổng Khuyến khích Loại 1",  "merit",      4_000_000.00, 3.60,
     "Dành cho SV có GPA >= 3.6/4.0 trong học kỳ trước. Trị giá 4 triệu VND/kỳ."),
    ("HB-KK2", "Học bổng Khuyến khích Loại 2",  "merit",      2_500_000.00, 3.20,
     "Dành cho SV có GPA từ 3.2 đến 3.59/4.0 trong học kỳ trước."),
    ("HB-HC",  "Học bổng Hỗ trợ Hoàn cảnh",     "need",       3_000_000.00, None,
     "Dành cho SV có hoàn cảnh khó khăn được nhà trường xét duyệt. Không yêu cầu GPA tối thiểu."),
    ("HB-DN",  "Học bổng Doanh nghiệp TechViet", "enterprise", 6_000_000.00, 3.50,
     "Do công ty TechViet tài trợ. Yêu cầu GPA >= 3.5 và cam kết thực tập tại công ty."),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_grade_letter(score: float) -> str:
    """Map a 0–10 numeric score to its letter grade per schema comment."""
    if score >= 8.5:
        return "A"
    if score >= 8.0:
        return "B+"
    if score >= 7.0:
        return "B"
    if score >= 6.5:
        return "C+"
    if score >= 5.5:
        return "C"
    if score >= 5.0:
        return "D+"
    if score >= 4.0:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


def _seed_departments(cur: psycopg2.extensions.cursor) -> None:
    cur.executemany(
        "INSERT INTO dim_department (department_code, department_name, faculty, head_name)"
        " VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        DEPARTMENTS,
    )
    log.info("Departments inserted.")


def _seed_majors(cur: psycopg2.extensions.cursor) -> None:
    cur.executemany(
        "INSERT INTO dim_major (major_code, major_name, faculty, total_credits_required, duration_years)"
        " VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        MAJORS,
    )
    log.info("Majors inserted.")


def _seed_semesters(cur: psycopg2.extensions.cursor) -> None:
    cur.executemany(
        "INSERT INTO dim_semester"
        " (semester_code, semester_name, academic_year, semester_number, start_date, end_date, is_current)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        SEMESTERS,
    )
    log.info("Semesters inserted.")


def _seed_courses(cur: psycopg2.extensions.cursor) -> None:
    cur.execute("SELECT department_code, department_id FROM dim_department")
    dept_map = {code: dept_id for code, dept_id in cur.fetchall()}

    rows = [
        (code, name, credits, dept_map[dept_code], desc, is_required, prereq)
        for code, name, credits, dept_code, desc, is_required, prereq in COURSES
    ]
    cur.executemany(
        "INSERT INTO dim_course"
        " (course_code, course_name, credits, department_id, description, is_required, prerequisites)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        rows,
    )
    log.info("Courses inserted.")


def _seed_scholarships(cur: psycopg2.extensions.cursor) -> None:
    cur.executemany(
        "INSERT INTO dim_scholarship"
        " (scholarship_code, scholarship_name, scholarship_type, amount, min_gpa, description)"
        " VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        SCHOLARSHIPS,
    )
    log.info("Scholarships inserted.")


def _seed_students(cur: psycopg2.extensions.cursor) -> None:
    cur.execute("SELECT major_id FROM dim_major")
    major_ids = [row[0] for row in cur.fetchall()]

    year_counter = {year: 1 for year in ADMISSION_YEARS}
    student_rows = []

    for _ in range(STUDENT_COUNT):
        admission_year = random.choices(ADMISSION_YEARS, weights=YEAR_WEIGHTS)[0]
        student_code = f"SV{admission_year}{year_counter[admission_year]:03d}"
        year_counter[admission_year] += 1

        gender = random.choice(["male", "female"])
        date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=24)
        current_gpa = round(random.uniform(1.0, 4.0), 2)
        total_credits_completed = random.randint(0, 90)
        status = random.choices(STUDENT_STATUS_OPTIONS, weights=STUDENT_STATUS_WEIGHTS)[0]

        student_rows.append((
            student_code,
            fake.name(),
            gender,
            date_of_birth,
            f"{student_code.lower()}@student.edu.vn",
            fake.phone_number()[:15],
            random.choice(major_ids),
            admission_year,
            current_gpa,
            total_credits_completed,
            status,
        ))

    cur.executemany(
        "INSERT INTO dim_student"
        " (student_code, full_name, gender, date_of_birth, email, phone,"
        "  major_id, admission_year, current_gpa, total_credits_completed, status)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        student_rows,
    )
    log.info("Students inserted: %d rows attempted.", len(student_rows))


def _seed_enrollments(cur: psycopg2.extensions.cursor) -> None:
    cur.execute("SELECT student_id FROM dim_student")
    student_ids = [row[0] for row in cur.fetchall()]

    cur.execute(
        "SELECT semester_id, is_current FROM dim_semester ORDER BY start_date"
    )
    semesters = cur.fetchall()

    cur.execute("SELECT course_id, credits FROM dim_course")
    all_courses = cur.fetchall()

    enrollment_count = 0
    skip_count = 0

    for student_id in student_ids:
        student_course_pool = random.sample(
            all_courses,
            min(len(all_courses), random.randint(COURSES_PER_STUDENT_MIN, COURSES_PER_STUDENT_MAX)),
        )

        for semester_id, is_current_semester in semesters:
            sem_courses = random.sample(
                student_course_pool,
                min(len(student_course_pool), random.randint(ENROLLMENTS_PER_SEM_MIN, ENROLLMENTS_PER_SEM_MAX)),
            )
            for course_id, course_credits in sem_courses:
                row = _build_enrollment_row(
                    student_id, course_id, semester_id, course_credits, is_current_semester
                )
                cur.execute("SAVEPOINT sp_enroll")
                try:
                    cur.execute(
                        "INSERT INTO fact_enrollment"
                        " (student_id, course_id, semester_id, grade, grade_letter, credits_earned, status)"
                        " VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        row,
                    )
                    cur.execute("RELEASE SAVEPOINT sp_enroll")
                    enrollment_count += 1
                except psycopg2.Error as exc:
                    cur.execute("ROLLBACK TO SAVEPOINT sp_enroll")
                    cur.execute("RELEASE SAVEPOINT sp_enroll")
                    log.warning("Enrollment skipped (student=%s course=%s sem=%s): %s",
                                student_id, course_id, semester_id, exc)
                    skip_count += 1

    log.info("Enrollments inserted: %d rows, %d skipped.", enrollment_count, skip_count)


def _build_enrollment_row(
    student_id: int,
    course_id: int,
    semester_id: int,
    course_credits: int,
    is_current_semester: bool,
) -> tuple:
    if is_current_semester:
        return (student_id, course_id, semester_id, None, None, 0, "in_progress")

    score = round(random.uniform(0.0, 10.0), 2)
    grade_letter = _resolve_grade_letter(score)
    passed = score >= PASSING_GRADE_THRESHOLD
    credits_earned = course_credits if passed else 0
    enrollment_status = "passed" if passed else "failed"
    return (student_id, course_id, semester_id, score, grade_letter, credits_earned, enrollment_status)


def _seed_scholarship_awards(cur: psycopg2.extensions.cursor) -> None:
    cur.execute("SELECT student_id, current_gpa FROM dim_student WHERE status = 'active'")
    active_students = cur.fetchall()

    cur.execute("SELECT scholarship_id, min_gpa, amount FROM dim_scholarship")
    scholarships = cur.fetchall()

    cur.execute(
        "SELECT semester_id FROM dim_semester"
        " WHERE is_current = FALSE ORDER BY start_date DESC LIMIT 2"
    )
    past_semester_ids = [row[0] for row in cur.fetchall()]

    if not past_semester_ids:
        log.warning("No past semesters found — scholarship awards skipped.")
        return

    award_count = 0
    skip_count = 0

    for student_id, student_gpa in active_students:
        for scholarship_id, min_gpa, scholarship_amount in scholarships:
            gpa_qualifies = min_gpa is None or float(student_gpa) >= float(min_gpa)
            if not gpa_qualifies:
                continue
            if random.random() >= SCHOLARSHIP_AWARD_PROBABILITY:
                continue

            awarded_semester_id = random.choice(past_semester_ids)
            cur.execute("SAVEPOINT sp_award")
            try:
                cur.execute(
                    "INSERT INTO fact_scholarship_award"
                    " (student_id, scholarship_id, semester_id, amount_awarded, awarded_at)"
                    " VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (student_id, scholarship_id, awarded_semester_id,
                     float(scholarship_amount), date.today()),
                )
                cur.execute("RELEASE SAVEPOINT sp_award")
                award_count += 1
            except psycopg2.Error as exc:
                cur.execute("ROLLBACK TO SAVEPOINT sp_award")
                cur.execute("RELEASE SAVEPOINT sp_award")
                log.warning("Award skipped (student=%s scholarship=%s): %s",
                            student_id, scholarship_id, exc)
                skip_count += 1

    log.info("Scholarship awards inserted: %d rows, %d skipped.", award_count, skip_count)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError("DATABASE_URL is not set. Add it to be/.env before running.")

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        _seed_departments(cur)
        _seed_majors(cur)
        _seed_semesters(cur)
        _seed_courses(cur)
        _seed_scholarships(cur)
        _seed_students(cur)
        _seed_enrollments(cur)
        _seed_scholarship_awards(cur)
        conn.commit()
        print("✅ Seed complete")
    except Exception:
        conn.rollback()
        log.exception("Seed failed — transaction rolled back.")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run()
