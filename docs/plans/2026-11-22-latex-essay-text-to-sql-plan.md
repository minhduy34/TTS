# LaTeX Academic Essay (Text-to-SQL) Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Xây dựng hoàn chỉnh bộ tiểu luận học thuật bằng LaTeX (`report/main.tex`, `report/references.bib`, `report/figures/*`) theo đúng đề cương 5 chương + Tóm tắt, bìa chuẩn `report/bìa.docx` (Sinh viên: Cái Minh Duy - MSSV: 4654110003), tích hợp lý thuyết/công thức/hình ảnh từ 2 bài báo `report/2312.11242v6.pdf` (MAC-SQL) và `report/2507.14372v1.pdf` (LinkedIn Enterprise Text-to-SQL) cùng thực nghiệm từ source code hiện tại (`fe_be/schema.sql`, `fe_be/seed.py`, `ai/src/`).

**Architecture:** Tổ chức dự án LaTeX nguyên khối tự chứa trong thư mục `report/` gồm tệp chính `report/main.tex` (tương thích 100% với `pdflatex` và Overleaf, dùng gói `vietnamese` babel, `tikz`, `pgfplots`, `amsmath`, `algorithm`, `listings`, `booktabs`), tệp tài liệu tham khảo `report/references.bib`, và thư mục hình ảnh `report/figures/`. Các sơ đồ kiến trúc hệ thống, lược đồ CSDL hình sao (Star Schema 8 bảng) và biểu đồ thực nghiệm được vẽ trực tiếp bằng vector TikZ/pgfplots kết hợp với hình ảnh trích xuất từ `bìa.docx` và 2 bài báo PDF.

**Tech Stack:** LaTeX (`report` class, `babel[vietnamese]`, `tikz`, `pgfplots`, `amsmath`, `algpseudocode`, `listings`, `booktabs`), BibTeX (`ieeetr`), PowerShell / Python (trích xuất hình ảnh và kiểm thử cú pháp LaTeX).

---

### Task 1: Trích xuất và chuẩn bị tài nguyên hình ảnh trong `report/figures/`

**Files:**
- Create: `report/figures/logo_qnu.png`
- Create: `report/figures/mac_sql_framework.png`
- Create: `report/figures/mac_sql_agents.png`
- Create: `report/figures/linkedin_kg_agent.png`
- Test: `report/verify_latex.ps1`

**Step 1: Viết script kiểm thử sự tồn tại và kích thước hợp lệ của tài nguyên hình ảnh**

Tạo tệp `report/verify_latex.ps1` để kiểm tra các tệp hình ảnh trong `report/figures/`:

```powershell
$ErrorActionPreference = "Stop"
$requiredFigures = @(
    "report/figures/logo_qnu.png"
)
foreach ($f in $requiredFigures) {
    if (-not (Test-Path $f)) {
        Write-Error "Missing required figure: $f"
        exit 1
    }
    $len = (Get-Item $f).Length
    if ($len -lt 1000) {
        Write-Error "Figure file too small ($len bytes): $f"
        exit 1
    }
}
Write-Output "PASS: Required figure assets verified."
```

**Step 2: Chạy script kiểm thử để xác nhận trạng thái FAIL ban đầu**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: FAIL với thông báo `Missing required figure: report/figures/logo_qnu.png`.

**Step 3: Trích xuất `word/media/image1.png` từ `report/bìa.docx` sang `report/figures/logo_qnu.png`**

Sử dụng `.NET System.IO.Compression.ZipFile` trong PowerShell để giải nén `word/media/image1.png` từ `report/bìa.docx` ra `report/figures/logo_qnu.png`.

**Step 4: Chạy lại script kiểm thử để xác nhận PASS**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: `PASS: Required figure assets verified.`

---

### Task 2: Xây dựng cơ sở dữ liệu tài liệu tham khảo `report/references.bib`

**Files:**
- Create: `report/references.bib`
- Modify: `report/verify_latex.ps1`

**Step 1: Bổ sung bài kiểm tra khóa trích dẫn BibTeX vào `report/verify_latex.ps1`**

Kiểm tra `report/references.bib` có đầy đủ các khóa trích dẫn bắt buộc: `zhong2017wikisql`, `yu2018spider`, `li2023bird`, `wang2020ratsql`, `pourreza2023dinsql`, `gao2023dailsql`, `wang2025macsql`, `chen2025enterprise`, `yao2023react`, `dong2023c3`, `tai2023cot`, `lei2024spider2`.

**Step 2: Chạy kiểm thử để xác nhận FAIL**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: FAIL do thiếu `report/references.bib`.

**Step 3: Viết tệp `report/references.bib` chuẩn BibTeX**

Tạo `report/references.bib` chứa đầy đủ thông tin xuất bản học thuật của các bài báo:
1. `zhong2017wikisql` — WikiSQL (Zhong et al., 2017)
2. `yu2018spider` — Spider (Yu et al., EMNLP 2018)
3. `li2023bird` — BIRD (Li et al., NeurIPS 2023)
4. `wang2020ratsql` — RAT-SQL (Wang et al., ACL 2020)
5. `pourreza2023dinsql` — DIN-SQL (Pourreza & Rafiei, NeurIPS 2023)
6. `gao2023dailsql` — DAIL-SQL (Gao et al., VLDB 2024 / arXiv 2023)
7. `wang2025macsql` — MAC-SQL (Wang et al., COLING 2024 / arXiv:2312.11242v6, 2025)
8. `chen2025enterprise` — Text-to-SQL for Enterprise Data Analytics (Chen et al., KDD '25 Workshop AAE '25 / arXiv:2507.14372v1, 2025)
9. `yao2023react` — ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., ICLR 2023)
10. `dong2023c3` — C3-SQL (Dong et al., 2023)
11. `tai2023cot` — Exploring Chain-of-Thought Style Prompting for Text-to-SQL (Tai et al., EMNLP 2023)
12. `lei2024spider2` — Spider 2.0 (Lei et al., 2024)

**Step 4: Chạy lại kiểm thử để xác nhận PASS**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: PASS.

---

### Task 3: Xây dựng Khung LaTeX, Trang bìa chuẩn `bìa.docx`, Tóm tắt, Chương 1 & Chương 2 trong `report/main.tex`

**Files:**
- Create: `report/main.tex`
- Modify: `report/verify_latex.ps1`

**Step 1: Cập nhật `report/verify_latex.ps1` để kiểm tra cấu trúc Trang bìa, Tóm tắt, Chương 1 và Chương 2**

Kiểm tra sự hiện diện của:
- Thông tin trang bìa: `TRƯỜNG ĐẠI HỌC QUY NHƠN`, `KHOA TOÁN VÀ THỐNG KÊ`, `XÂY DỰNG HỆ THỐNG TEXT-TO-SQL HỖ TRỢ TRUY VẤN DỮ LIỆU`, `Xử lý Ngôn ngữ Tự nhiên (NLP)`, `TS. Lê Quang Hùng`, `Cái Minh Duy`, `4654110003`, `Khoa học Dữ liệu - Khóa K46`.
- Phần Tóm tắt (Abstract), Chương 1 (1.1, 1.2, 1.3) và Chương 2 (2.1, 2.2) cùng các công thức toán học (1)–(5) và sơ đồ TikZ minh họa khung MAC-SQL & Knowledge Graph.

**Step 2: Chạy kiểm thử để xác nhận FAIL**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: FAIL.

**Step 3: Viết Preamble, Trang bìa, Tóm tắt, Chương 1 và Chương 2 vào `report/main.tex`**

Bao gồm:
- Preamble đầy đủ gói lệnh tiếng Việt, toán học, bảng biểu, mã nguồn và đồ họa TikZ/pgfplots.
- Trang bìa có khung viền đôi TikZ, logo `figures/logo_qnu.png` và thông tin sinh viên `Cái Minh Duy` (`4654110003`).
- Tóm tắt (Abstract), Mục lục, Danh mục hình vẽ, Danh mục bảng biểu, Danh mục thuật ngữ viết tắt.
- Chương 1 (Giới thiệu: 1.1 Bối cảnh & Đặt vấn đề, 1.2 Các thách thức cốt lõi, 1.3 Mục tiêu & Đóng góp).
- Chương 2 (Cơ sở lý thuyết & Nghiên cứu liên quan: 2.1 Định nghĩa toán học Text-to-SQL & các bộ dữ liệu chuẩn WikiSQL, Spider, BIRD, Spider 2.0; 2.2 Các hướng tiếp cận RAT-SQL, DIN-SQL, DAIL-SQL, MAC-SQL với đầy đủ công thức Selector/Decomposer/Refiner/SQL-Llama, và Enterprise Text-to-SQL của LinkedIn kèm sơ đồ TikZ minh họa).

**Step 4: Chạy kiểm thử để xác nhận PASS**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: PASS.

---

### Task 4: Hoàn thiện Chương 3, Chương 4, Chương 5 và Kiểm tra Cân bằng Cú pháp LaTeX toàn cục

**Files:**
- Modify: `report/main.tex`
- Modify: `report/verify_latex.ps1`

**Step 1: Cập nhật `report/verify_latex.ps1` để kiểm tra Chương 3, 4, 5 và trình kiểm tra cân bằng môi trường LaTeX (`\begin{...}` / `\end{...}`)**

Kiểm tra:
- Chương 3 (3.1 Thiết kế & chuẩn hóa CSDL Star Schema 8 bảng từ `fe_be/schema.sql`, Schema Annotation tiếng Việt & truy vấn `pg_class`; 3.2 Kiến trúc tổng thể hệ thống từ `ai/src/`, Sơ đồ ERD TikZ, Sơ đồ System Pipeline TikZ, Giải thuật phối hợp đa tác tử, Selector, Decomposer CoT, Refiner & Dual Guardrails).
- Chương 4 (4.1 Thiết lập thực nghiệm 60 câu hỏi theo 4 mức Easy/Medium/Hard/Extra Hard, cấu hình `gemini-3.5-flash-lite` `temperature=0`; 4.2 Độ đo EM, EX, Latency; 4.3 Bảng & Biểu đồ `pgfplots` Ablation Study, hiệu năng Connection Pool & Schema Cache, Bảng & Ví dụ Phân tích lỗi Error Analysis).
- Chương 5 (5.1 Kết luận; 5.2 Hạn chế & Hướng phát triển: RAG cell values, Knowledge Graph indexing, Fine-tuning SLM).
- Kiểm tra cân bằng tuyệt đối tất cả cặp `\begin{env}` và `\end{env}`, cặp ngoặc `{}` và trích dẫn `\cite{...}` khớp 100% với `report/references.bib`.

**Step 2: Chạy kiểm thử để xác nhận FAIL**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: FAIL do chưa có Chương 3, 4, 5.

**Step 3: Viết đầy đủ Chương 3, Chương 4, Chương 5 và Tài liệu tham khảo vào `report/main.tex`**

Viết chi tiết, học thuật, có dẫn chứng mã nguồn thực tế (`fe_be/schema.sql`, `fe_be/seed.py`, `ai/src/agent/tools/sql_tools.py`, `ai/src/agent/subagents/sql_query_agent.py`, `ai/src/agent/tools/agent_tools.py`, `ai/src/main.py`), số liệu từ 2 bài báo PDF và biểu đồ `pgfplots`.

**Step 4: Chạy kiểm thử toàn diện để xác nhận PASS**

Run: `powershell -ExecutionPolicy Bypass -File "report/verify_latex.ps1"`
Expected: PASS với báo cáo kiểm tra 100% chương mục, hình vẽ, công thức, bảng biểu, trích dẫn BibTeX và cân bằng môi trường LaTeX.
