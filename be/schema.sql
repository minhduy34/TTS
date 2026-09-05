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
COMMENT ON COLUMN dim_major.major_id                IS 'ID ngành học, khóa chính';
COMMENT ON COLUMN dim_major.major_code             IS 'Mã ngành viết tắt, ví dụ: CNTT, KTPM, HTTT';
COMMENT ON COLUMN dim_major.major_name             IS 'Tên đầy đủ của ngành, ví dụ: Công nghệ Thông tin';
COMMENT ON COLUMN dim_major.faculty                IS 'Tên khoa quản lý ngành học';
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
COMMENT ON COLUMN dim_department.department_id   IS 'ID khoa/bộ môn, khóa chính';
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
COMMENT ON COLUMN dim_semester.semester_id     IS 'ID học kỳ, khóa chính';
COMMENT ON COLUMN dim_semester.semester_code   IS 'Mã học kỳ dạng HK1-2024-2025';
COMMENT ON COLUMN dim_semester.semester_name   IS 'Tên hiển thị đầy đủ, ví dụ: Học kỳ 1 năm học 2024-2025';
COMMENT ON COLUMN dim_semester.academic_year   IS 'Năm học định dạng YYYY-YYYY, ví dụ: 2024-2025';
COMMENT ON COLUMN dim_semester.semester_number IS 'Số thứ tự học kỳ trong năm: 1, 2, hoặc 3 (học kỳ hè)';
COMMENT ON COLUMN dim_semester.start_date      IS 'Ngày bắt đầu học kỳ';
COMMENT ON COLUMN dim_semester.end_date        IS 'Ngày kết thúc học kỳ';
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
COMMENT ON COLUMN dim_student.student_id              IS 'ID sinh viên, khóa chính';
COMMENT ON COLUMN dim_student.student_code            IS 'Mã sinh viên duy nhất, định dạng SV + năm + số thứ tự, ví dụ: SV2021001';
COMMENT ON COLUMN dim_student.full_name               IS 'Họ và tên đầy đủ của sinh viên';
COMMENT ON COLUMN dim_student.gender                  IS 'Giới tính: male (nam), female (nữ), other (khác)';
COMMENT ON COLUMN dim_student.date_of_birth           IS 'Ngày tháng năm sinh của sinh viên';
COMMENT ON COLUMN dim_student.email                   IS 'Địa chỉ email cá nhân của sinh viên';
COMMENT ON COLUMN dim_student.phone                   IS 'Số điện thoại liên lạc của sinh viên';
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
COMMENT ON COLUMN dim_course.course_id     IS 'ID học phần, khóa chính';
COMMENT ON COLUMN dim_course.course_code   IS 'Mã học phần duy nhất, ví dụ: CS101, MATH201, ENG301';
COMMENT ON COLUMN dim_course.course_name   IS 'Tên đầy đủ của học phần';
COMMENT ON COLUMN dim_course.credits       IS 'Số tín chỉ của học phần, từ 1 đến 4';
COMMENT ON COLUMN dim_course.department_id IS 'Khoa/bộ môn phụ trách giảng dạy học phần này';
COMMENT ON COLUMN dim_course.description   IS 'Mô tả chi tiết nội dung, mục tiêu của học phần';
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
COMMENT ON COLUMN dim_scholarship.scholarship_id   IS 'ID loại học bổng, khóa chính';
COMMENT ON COLUMN dim_scholarship.scholarship_code IS 'Mã học bổng, ví dụ: HB001, HB002';
COMMENT ON COLUMN dim_scholarship.scholarship_name IS 'Tên đầy đủ của loại học bổng';
COMMENT ON COLUMN dim_scholarship.scholarship_type IS 'Loại học bổng: merit (học lực), need (hoàn cảnh khó khăn), enterprise (doanh nghiệp tài trợ)';
COMMENT ON COLUMN dim_scholarship.amount           IS 'Giá trị học bổng mỗi học kỳ, đơn vị VND';
COMMENT ON COLUMN dim_scholarship.min_gpa          IS 'GPA tối thiểu trên thang 4.0 để đủ điều kiện xét. NULL nếu không yêu cầu GPA.';
COMMENT ON COLUMN dim_scholarship.description      IS 'Mô tả chi tiết điều kiện, tiêu chí để được nhận học bổng này';

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
COMMENT ON COLUMN fact_enrollment.enrollment_id IS 'ID đăng ký học phần, khóa chính';
COMMENT ON COLUMN fact_enrollment.student_id    IS 'ID sinh viên, khóa ngoại tham chiếu đến dim_student';
COMMENT ON COLUMN fact_enrollment.course_id     IS 'ID học phần, khóa ngoại tham chiếu đến dim_course';
COMMENT ON COLUMN fact_enrollment.semester_id   IS 'ID học kỳ, khóa ngoại tham chiếu đến dim_semester';
COMMENT ON COLUMN fact_enrollment.grade         IS 'Điểm số trên thang 10. NULL nếu học kỳ chưa kết thúc (status = in_progress).';
COMMENT ON COLUMN fact_enrollment.grade_letter  IS 'Điểm chữ: A (>=8.5), B+ (8.0-8.4), B (7.0-7.9), C+ (6.5-6.9), C (5.5-6.4), D+ (5.0-5.4), D (4.0-4.9), F (<4.0)';
COMMENT ON COLUMN fact_enrollment.credits_earned IS 'Số tín chỉ đạt được: bằng credits của dim_course nếu passed, bằng 0 nếu failed hoặc withdrawn';
COMMENT ON COLUMN fact_enrollment.status        IS 'Trạng thái: passed (qua môn), failed (trượt), in_progress (đang học), withdrawn (rút môn)';
COMMENT ON COLUMN fact_enrollment.registered_at IS 'Thời điểm sinh viên đăng ký học phần';

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
COMMENT ON COLUMN fact_scholarship_award.award_id       IS 'ID phần thưởng học bổng, khóa chính';
COMMENT ON COLUMN fact_scholarship_award.student_id     IS 'ID sinh viên nhận học bổng, khóa ngoại tham chiếu đến dim_student';
COMMENT ON COLUMN fact_scholarship_award.scholarship_id IS 'ID loại học bổng, khóa ngoại tham chiếu đến dim_scholarship';
COMMENT ON COLUMN fact_scholarship_award.semester_id    IS 'ID học kỳ nhận học bổng, khóa ngoại tham chiếu đến dim_semester';
COMMENT ON COLUMN fact_scholarship_award.amount_awarded IS 'Số tiền học bổng thực tế được trao, đơn vị VND.';
COMMENT ON COLUMN fact_scholarship_award.awarded_at     IS 'Ngày cấp học bổng cho sinh viên';
