# KỊCH BẢN THUYẾT TRÌNH — XÂY DỰNG HỆ THỐNG TEXT-TO-SQL HỖ TRỢ TRUY VẤN DỮ LIỆU

**Người trình bày:** Cái Minh Duy – MSSV 4654110003  
**Học phần:** Xử lý Ngôn ngữ Tự nhiên – GVHD: TS. Lê Quang Hùng  
**Tổng thời lượng:** khoảng 13–15 phút (15 slide, trung bình ~1 phút/slide)  
**File slide:** `Slide_Text_to_SQL_Cai_Minh_Duy_4654110003.pdf`

> Ghi chú: phần *in nghiêng trong ngoặc* là gợi ý thao tác/ngữ điệu. Phần còn lại là lời nói, có thể đọc nguyên văn hoặc diễn đạt lại theo ý mình.

---

## Slide 1 — Trang bìa (≈ 30 giây)
Xin chào thầy và các bạn. Em là Cái Minh Duy, mã số sinh viên 4654110003. Hôm nay em xin trình bày đề tài **"Xây dựng hệ thống Text-to-SQL hỗ trợ truy vấn dữ liệu"**, thuộc học phần Xử lý Ngôn ngữ Tự nhiên, dưới sự hướng dẫn của thầy Lê Quang Hùng.

Đề tài xây dựng một hệ thống cho phép người dùng **hỏi bằng tiếng Việt** và nhận câu trả lời lấy trực tiếp từ cơ sở dữ liệu, dựa trên kiến trúc **đa tác tử MAC-SQL** kết hợp mô hình ngôn ngữ lớn.

---

## Slide 2 — Bối cảnh và vấn đề (≈ 1 phút)
Dữ liệu học vụ của trường đại học như sinh viên, học phần, điểm số, học bổng đều nằm trong cơ sở dữ liệu quan hệ. Muốn lấy thông tin, người dùng phải biết SQL, mà đa số sinh viên, cố vấn học tập hay cán bộ quản lý **không biết SQL**. Báo cáo cố định thì không đáp ứng được các câu hỏi đột xuất.

Bài toán **Text-to-SQL** giải quyết việc này: tự động biến câu hỏi tự nhiên thành câu lệnh SQL. *(Chỉ vào khung ví dụ bên phải.)* Ví dụ câu hỏi "Bao nhiêu sinh viên trượt Giải tích 1?" sẽ được chuyển thành một câu lệnh `SELECT COUNT(DISTINCT ...)` trên bảng đăng ký học phần.

---

## Slide 3 — Ba thách thức cốt lõi (≈ 1 phút)
Bài toán này có ba khó khăn chính.

**Thứ nhất, ngôn ngữ nhập nhằng.** Người dùng nói "rớt môn", "trượt môn" hay "không đạt" đều có nghĩa là trạng thái `failed` trong cơ sở dữ liệu.

**Thứ hai, liên kết lược đồ – Schema Linking.** Câu hỏi bằng tiếng Việt nhưng tên bảng, tên cột lại bằng tiếng Anh, và để trả lời có khi phải nối qua ba, bốn bảng.

**Thứ ba, tính đúng đắn khi thực thi.** Câu lệnh có thể đúng ngữ pháp nhưng sai cú pháp của hệ quản trị, trả về kết quả rỗng, hoặc gây rủi ro an toàn dữ liệu.

---

## Slide 4 — Mục tiêu và đóng góp (≈ 45 giây)
Từ đó, đề tài đặt ra bốn mục tiêu:
1. Thiết kế cơ sở dữ liệu học vụ dạng **Star Schema** gồm 8 bảng, kèm chú thích ngữ nghĩa tiếng Việt.
2. Triển khai kiến trúc **đa tác tử** gồm Selector, Decomposer và Refiner.
3. Xây dựng **bộ benchmark tự động** 20 câu hỏi, chia 4 mức độ khó, đo bằng EX, EM và CSR.
4. Kiểm thử **toàn trình End-to-End** trên hai dịch vụ FastAPI.

---

## Slide 5 — Phát biểu bài toán và bộ dữ liệu chuẩn (≈ 1 phút)
Về mặt hình thức, Text-to-SQL là một ánh xạ: đầu vào là câu hỏi **Q** và lược đồ cơ sở dữ liệu **S**, đầu ra là câu lệnh SQL **Y**.

Có ba bộ dữ liệu chuẩn thường dùng. **WikiSQL** năm 2017, chỉ có truy vấn đơn bảng. **Spider** năm 2018, truy vấn nhiều bảng, nhiều miền, có lồng nhau; đề tài dùng chuẩn độ khó của Spider để phân loại câu hỏi. **BIRD** năm 2023, cơ sở dữ liệu lớn, dữ liệu nhiễu và cần tri thức nghiệp vụ.

---

## Slide 6 — Các hướng tiếp cận (≈ 1 phút)
Các phương pháp phát triển qua ba giai đoạn.

Giai đoạn đầu dùng **mạng nơ-ron**, tiêu biểu là RAT-SQL mã hóa quan hệ giữa các bảng và cột. Giai đoạn hai dùng **mô hình ngôn ngữ lớn với prompt**: DIN-SQL phân rã bài toán thành các bước và có tự sửa lỗi, DAIL-SQL tối ưu cách biểu diễn lược đồ và chọn ví dụ mẫu. Giai đoạn ba là **đa tác tử**, đại diện là **MAC-SQL**, cũng là nền tảng trực tiếp của đề tài. Ý tưởng chính là chia việc cho các tác tử chuyên biệt để giảm tải ngữ cảnh và tăng độ chính xác.

---

## Slide 7 — MAC-SQL: ba tác tử cộng tác (≈ 1 phút)
MAC-SQL có ba tác tử.

**Selector** lọc ra những bảng và cột liên quan, bỏ phần nhiễu. **Decomposer** phân rã câu hỏi phức tạp theo chuỗi tư duy rồi sinh câu lệnh SQL. **Refiner** thực thi câu lệnh, đọc thông báo lỗi và **tự sửa**, tối đa ba lần.

Ngoài ra, em tham khảo thêm bài báo của LinkedIn: việc **mô tả ngữ nghĩa cho bảng và cột** giúp chất lượng truy vấn tăng từ 9% lên 48%. Đây là lý do em bổ sung chú thích tiếng Việt cho toàn bộ cơ sở dữ liệu.

---

## Slide 8 — Cơ sở dữ liệu học vụ Star Schema (≈ 1 phút)
*(Chỉ vào sơ đồ.)* Cơ sở dữ liệu có một bảng sự kiện trung tâm là `fact_enrollment`, ghi lại mỗi lần sinh viên đăng ký một học phần, nối với các bảng chiều như sinh viên, học phần, học kỳ; sinh viên nối với ngành, học phần nối với khoa. Ngoài ra còn bảng học bổng.

Tổng cộng **8 bảng, 2.958 bản ghi**, trong đó đăng ký học phần có 2.769 bản ghi, 39 suất học bổng, 100 sinh viên và 30 học phần. Mọi bảng, mọi cột đều có chú thích tiếng Việt bằng `COMMENT ON` để mô hình hiểu đúng ý nghĩa.

---

## Slide 9 — Kiến trúc hệ thống (≈ 1 phút 15 giây)
*(Đi theo mũi tên từ trái sang phải.)* Người dùng nhập câu hỏi trên giao diện web ở cổng 8000. **Deep Agent** nhận câu hỏi, phân loại ý định: nếu ngoài phạm vi thì từ chối ngay, nếu có thời gian tương đối như "tháng trước" thì đổi sang ngày cụ thể. Sau đó câu hỏi chuyển cho **SQL Agent**, thực hiện chọn lọc lược đồ và suy luận từng bước. Câu lệnh được thực thi qua công cụ `execute_sql` ở chế độ chỉ đọc.

Nếu có lỗi hoặc kết quả rỗng, hệ thống quay lại sửa, như đường nét đứt màu đỏ. Hệ thống chạy trên **LangGraph và Gemini** với `temperature = 0`, hai dịch vụ FastAPI giao tiếp qua SSE.

---

## Slide 10 — Ba thành phần chính và rào chắn an toàn (≈ 1 phút)
Về chức năng: công cụ `get_schema` trả về lược đồ kèm chú thích và khóa ngoại, được lưu đệm trong RAM; câu hỏi được phân rã năm bước từ mục tiêu, cột cần chọn, đường nối bảng, điều kiện lọc đến gom nhóm và sắp xếp; công cụ `resolve_time_range` đổi "tháng trước" thành khoảng ngày chính xác.

Về an toàn, `execute_sql` chỉ cho phép `SELECT` hoặc `WITH`, chặn nhiều câu lệnh nối bằng dấu chấm phẩy, mở phiên **chỉ đọc**, giới hạn 10 giây và tối đa 200 dòng. Nhờ vậy mô hình không thể sửa hay xóa dữ liệu.

---

## Slide 11 — Thiết lập thực nghiệm và độ đo (≈ 1 phút 15 giây)
Em xây bộ kiểm thử gồm **20 câu hỏi tiếng Việt tự nhiên**, chia đều 4 mức độ: Easy, Medium, Hard, Extra Hard, mỗi mức 5 câu, chạy hoàn toàn tự động bằng `run_benchmark.py`.

Ba độ đo chính:
- **EX – Execution Accuracy:** câu SQL dự đoán và câu chuẩn cho **cùng kết quả** khi chạy trên cơ sở dữ liệu.
- **EM – Exact Set Match:** so khớp cấu trúc từng mệnh đề SQL.
- **CSR – Compilation Success Rate:** tỷ lệ câu lệnh chạy không lỗi.

Em so sánh ba cấu hình: Baseline, thêm Schema Selector, và Full Pipeline.

---

## Slide 12 — Kết quả Ablation Study (≈ 1 phút 15 giây)
*(Chỉ vào từng dòng của bảng.)* Baseline chỉ đạt **EX 45%**, vì mô hình phải đoán giá trị như "Failed" hay "Đang học", thậm chí sinh cú pháp không chạy được trên SQLite nên CSR chỉ 90%.

Khi thêm Schema Selector và chú thích, EX tăng gấp đôi lên **90%**. Với Full Pipeline, EX đạt **95%** và CSR đạt **100%**. EM giữ ở 85% vì nhiều câu đúng kết quả nhưng viết khác câu chuẩn. Độ trễ trung bình khoảng 1 giây.

Như vậy, so với Baseline, hệ thống tăng **50 điểm phần trăm EX**, và đóng góp lớn nhất đến từ chú thích ngữ nghĩa.

---

## Slide 13 — EX theo mức độ khó (≈ 45 giây)
*(Chỉ vào biểu đồ.)* Biểu đồ cho thấy sự khác biệt rõ nhất ở các câu khó. Ở mức **Hard**, Baseline chỉ đạt 20%, trong khi Full Pipeline đạt **100%**. Ở mức **Extra Hard**, từ 20% lên **80%**. Hai mức Easy và Medium đều đạt 100% khi có chú thích lược đồ. Điều này cho thấy các câu phức tạp hưởng lợi nhiều nhất từ kiến trúc đa tác tử.

---

## Slide 14 — Ca điển hình và kiểm thử E2E (≈ 1 phút 30 giây)
Bên trái là một ca điển hình, câu **H05**: "bao nhiêu sinh viên qua môn *Cấu trúc dữ liệu và giải thuật*". Trong cơ sở dữ liệu, tên môn lưu là "Cấu trúc Dữ liệu **&** Giải thuật". Lần đầu, mô hình lọc theo tên người dùng gõ nên được **0 kết quả**. Refiner phát hiện bất thường, đối chiếu danh mục học phần, đổi sang mã `CS102` và lần thứ hai trả về đúng **24 sinh viên**. Hai cấu hình còn lại không làm được việc này.

Bên phải là kiểm thử **End-to-End**: cả hai dịch vụ ở cổng 8000 và 8001 trả `200 OK`; câu hỏi thống kê theo ngành và câu "trượt Giải tích 1" cho kết quả đúng, 11 sinh viên; câu hỏi về thời tiết bị từ chối đúng cách mà không gọi truy vấn nào.

---

## Slide 15 — Kết luận và hướng phát triển (≈ 1 phút)
**Kết luận:** Full Pipeline đạt **EX 95%** và **CSR 100%**. Chú thích lược đồ nâng EX từ 45% lên 90%, còn Refiner xử lý được các lỗi lệch tên thực thể.

**Hạn chế và hướng phát triển:**
- Độ trễ do các tác tử chạy tuần tự → có thể song song hóa.
- Lệch giá trị trong ô dữ liệu → tích hợp **RAG** để tra cứu giá trị thực tế.
- Chi phí token → tinh chỉnh các mô hình mã nguồn mở cỡ nhỏ.

Em xin chân thành cảm ơn thầy và các bạn đã lắng nghe. Em sẵn sàng trả lời câu hỏi ạ.

---

# PHỤ LỤC — CÂU HỎI THƯỜNG GẶP VÀ GỢI Ý TRẢ LỜI

**1. Tập kiểm thử chỉ có 20 câu, có đủ tin cậy không?**  
Đây là tập quy mô nhỏ, em dùng để kiểm chứng xu hướng, nên số liệu phản ánh mức cải thiện tương đối giữa các cấu hình chứ không đại diện cho mọi tình huống. Hướng mở rộng là tăng số câu hỏi và dùng thêm tập như Spider hoặc BIRD.

**2. Vì sao EM thấp hơn EX?**  
EM so khớp cấu trúc nên phạt cả những câu viết khác cách nhưng cho cùng kết quả, ví dụ dùng bí danh khác, `LEFT JOIN` thay `JOIN`. EX so sánh kết quả thực thi nên phản ánh đúng trải nghiệm người dùng hơn.

**3. Vì sao dùng SQLite cục bộ mà báo cáo nói về PostgreSQL/Supabase?**  
Hệ thống hỗ trợ cả hai. Khi chạy thực nghiệm, cơ sở dữ liệu Supabase không kết nối được, nên em dùng bản SQLite cục bộ có dữ liệu giống hệt, được tạo từ cùng `schema.sql` và `seed.py` với `random.seed(42)`, giữ nguyên chú thích tiếng Việt.

**4. Refiner có sửa được mọi lỗi không?**  
Chưa. Refiner chỉ kích hoạt khi có lỗi thực thi hoặc kết quả rỗng/bằng 0. Với lỗi "câm" như câu **X05**, câu lệnh chạy được nhưng đặt sai phạm vi điều kiện lọc, nên kết quả khác chuẩn mà hệ thống không tự phát hiện.

**5. Tại sao đặt `temperature = 0`?**  
Để kết quả ổn định, ít ngẫu nhiên khi sinh SQL, giúp kết quả thực nghiệm dễ tái lập.

**6. Hệ thống đảm bảo an toàn dữ liệu thế nào?**  
Ba lớp: chặn nhiều câu lệnh, chỉ cho phép `SELECT`/`WITH`, và mở kết nối chỉ đọc với giới hạn thời gian và số dòng.

**7. Đóng góp riêng của đề tài so với MAC-SQL gốc là gì?**  
Áp dụng vào miền học vụ tiếng Việt; kết hợp chú thích ngữ nghĩa theo hướng của LinkedIn; thêm Deep Agent để phân loại ý định và phân giải thời gian; có benchmark tự động và kiểm thử E2E.

---

# BẢNG PHÂN BỔ THỜI GIAN

| Slide | Nội dung | Thời gian |
|:---:|---|:---:|
| 1 | Bìa | 0:30 |
| 2 | Bối cảnh, vấn đề | 1:00 |
| 3 | Ba thách thức | 1:00 |
| 4 | Mục tiêu | 0:45 |
| 5 | Bài toán, bộ dữ liệu | 1:00 |
| 6 | Hướng tiếp cận | 1:00 |
| 7 | MAC-SQL | 1:00 |
| 8 | Star Schema | 1:00 |
| 9 | Kiến trúc | 1:15 |
| 10 | Thành phần, an toàn | 1:00 |
| 11 | Thiết lập, độ đo | 1:15 |
| 12 | Kết quả Ablation | 1:15 |
| 13 | EX theo mức khó | 0:45 |
| 14 | Ca điển hình, E2E | 1:30 |
| 15 | Kết luận | 1:00 |
| | **Tổng** | **≈ 15:15** |

> Nếu cần rút ngắn xuống còn 10 phút: lướt nhanh slide 5, 6 và 10 (mỗi slide còn khoảng 30 giây).
