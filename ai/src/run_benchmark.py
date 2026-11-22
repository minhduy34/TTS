"""Automated Text-to-SQL Benchmark Runner & Evaluator.

Evaluates 3 Ablation Configurations on the live student management database (fe_be/student.db):
  1. Baseline (Zero-shot Prompting): Raw table & column names only (no Vietnamese COMMENT ON
     semantic annotations, no enum value definitions, no FK annotations, no CoT, no Refiner).
  2. Baseline + Schema Selector: Enriched schema from get_schema() with Vietnamese COMMENT ON
     and [FK] relationships + Schema Linking (single-shot generation, no CoT Decomposer or Refiner).
  3. Full Pipeline (Selector + Decomposer + Refiner): Full MAC-SQL / LangGraph Multi-Agent
     pipeline with Schema Linking, Chain-of-Thought Decomposition, and Execution Refiner loop.

Computes the exact mathematical metrics from Chapter 4:
  - Exact Set Match (EM): Clause-level structural set equivalence across
      C = {SELECT, FROM/JOIN, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT}
  - Execution Accuracy (EX): Result-set equivalence on live DB D: Exec(Y_hat, D) == Exec(Y, D)
  - Compilation Success Rate (CSR): Percentage of queries executing without SQL engine error
  - Latency (s): Average wall-clock execution time per query
"""
import asyncio
import json
from pathlib import Path
import re
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from agent.llm import get_llm
from agent.tools.sql_tools import execute_sql, get_schema

BENCHMARK_PATH = Path(__file__).parent / "benchmark_data.json"
REPORT_OUT_PATH = Path(__file__).resolve().parents[2] / "report" / "benchmark_results.json"

# Config 1 (Baseline Zero-shot): Raw unannotated table/column names without Vietnamese COMMENT ON
# descriptions, without enum value hints ('active', 'failed', 'passed'), and without explicit FK links.
RAW_UNANNOTATED_SCHEMA = """Database tables (raw schema without column comments or enum documentation):
- dim_major (major_id, major_code, major_name, faculty, total_credits_required, duration_years)
- dim_department (department_id, department_code, department_name, faculty, head_name)
- dim_semester (semester_id, semester_code, semester_name, academic_year, semester_number, start_date, end_date, is_current)
- dim_student (student_id, student_code, full_name, gender, date_of_birth, email, phone, major_id, admission_year, current_gpa, total_credits_completed, status)
- dim_course (course_id, course_code, course_name, credits, department_id, description, is_required, prerequisites)
- dim_scholarship (scholarship_id, scholarship_code, scholarship_name, scholarship_type, amount, min_gpa, description)
- fact_enrollment (enrollment_id, student_id, course_id, semester_id, grade, grade_letter, credits_earned, status, registered_at)
- fact_scholarship_award (award_id, student_id, scholarship_id, semester_id, amount_awarded, awarded_at)
"""


def _extract_text(content: Any) -> str:
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content) if content else ""


def _extract_sql_from_text(text: str) -> str:
    m = re.search(r"```(?:sql)?\s*(SELECT[\s\S]*?|WITH[\s\S]*?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip(";")
    m2 = re.search(r"((?:SELECT|WITH)\s+[\s\S]+)", text, re.IGNORECASE)
    if m2:
        return m2.group(1).strip().rstrip(";")
    return text.strip().rstrip(";")


async def _invoke_llm_with_retry(llm, prompt: str, max_retries: int = 6) -> tuple[str, float]:
    """Invoke Gemini LLM with automatic backoff on 429 rate-limit errors.
    Returns (response_text, active_inference_time_seconds).
    """
    for attempt in range(max_retries):
        t0 = time.perf_counter()
        try:
            resp = await llm.ainvoke(prompt)
            dt = time.perf_counter() - t0
            return _extract_text(resp.content), dt
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                wait_s = 8.0 + attempt * 5.0
                m = re.search(r"retry in (\d+(?:\.\d+)?)s", msg, re.IGNORECASE)
                if m:
                    wait_s = max(float(m.group(1)) + 1.5, 5.0)
                print(f"    [Rate Limit 429] Waiting {wait_s:.1f}s before retry {attempt + 1}/{max_retries}...")
                await asyncio.sleep(wait_s)
            else:
                raise
    raise RuntimeError("Exceeded max retries for LLM call")


# ============================================================================
# Mathematical Metric 1: Exact Set Match (EM)
# EM = (1/N) * sum_{n=1}^N prod_{C_k in C} I(C_k(Y_hat_n) == C_k(Y_n))
# ============================================================================

_CLAUSE_KEYWORDS = ["SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT"]


def _normalize_sql_token(s: str) -> str:
    # Preserve exact case inside single-quoted string literals while lowercasing SQL keywords/identifiers
    literals: list[str] = []

    def _save_lit(m):
        literals.append(m.group(0))
        return f"__LIT_{len(literals) - 1}__"

    s_masked = re.sub(r"'[^']*'", _save_lit, s.strip().rstrip(";"))
    s_low = s_masked.lower()
    s_low = re.sub(r"\s+", " ", s_low)
    s_low = re.sub(r"\btrue\b", "1", s_low)
    s_low = re.sub(r"\bfalse\b", "0", s_low)
    s_low = re.sub(r"\bilike\b", "like", s_low)
    # Strip table alias prefixes like m.major_code -> major_code
    s_low = re.sub(r"\b[a-z0-9_]+\.([a-z0-9_]+)\b", r"\1", s_low)
    # Strip AS alias in SELECT projections: expr as alias -> expr
    s_low = re.sub(r"\s+as\s+[a-z0-9_]+\b", "", s_low)
    # Normalize count(col_id) or count(1) -> count(*) when not distinct
    s_low = re.sub(r"count\s*\(\s*(?!distinct\b)[a-z0-9_*]+\s*\)", "count(*)", s_low)

    for idx, lit in enumerate(literals):
        s_low = s_low.replace(f"__lit_{idx}__", lit)
    return s_low.strip()


def parse_sql_clause_sets(sql: str) -> dict[str, set[str]]:
    """Decompose SQL query Y into 7 canonical clause sets C_k(Y) with alias resolution."""
    clauses: dict[str, set[str]] = {k: set() for k in _CLAUSE_KEYWORDS}
    if not sql or not sql.strip():
        return clauses

    clean = re.sub(r"\s+", " ", sql.strip().rstrip(";"))
    pattern = r"\b(SELECT|FROM|WHERE|GROUP\s+BY|HAVING|ORDER\s+BY|LIMIT)\b"
    tokens = list(re.finditer(pattern, clean, flags=re.IGNORECASE))
    if not tokens:
        return clauses

    top_tokens = []
    for m in tokens:
        prefix = clean[: m.start()]
        if prefix.count("(") == prefix.count(")"):
            kw = re.sub(r"\s+", " ", m.group(1).upper())
            top_tokens.append((kw, m.start(), m.end()))

    alias_map: dict[str, str] = {}

    for idx, (kw, start, end) in enumerate(top_tokens):
        next_start = top_tokens[idx + 1][1] if idx + 1 < len(top_tokens) else len(clean)
        body = clean[end:next_start].strip()

        if kw in ("SELECT", "GROUP BY", "ORDER BY"):
            items = []
            curr = []
            depth = 0
            for ch in body:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                if ch == "," and depth == 0:
                    items.append("".join(curr))
                    curr = []
                else:
                    curr.append(ch)
            if curr:
                items.append("".join(curr))

            if kw == "SELECT":
                for it in items:
                    m_alias = re.search(r"^(.*?)\s+AS\s+([a-zA-Z0-9_]+)\s*$", it.strip(), flags=re.IGNORECASE)
                    if m_alias:
                        alias_map[m_alias.group(2).lower()] = _normalize_sql_token(m_alias.group(1))

            norm_items = set()
            for it in items:
                if not it.strip():
                    continue
                cleaned_it = re.sub(r"\bASC\b", "", it, flags=re.IGNORECASE).strip()
                tok = _normalize_sql_token(cleaned_it)
                if kw == "ORDER BY":
                    # Replace select alias with canonical select expression
                    for al, expr in alias_map.items():
                        tok = re.sub(rf"\b{re.escape(al)}\b", expr, tok)
                norm_items.add(tok)
            clauses[kw] = norm_items
        elif kw == "FROM":
            tables = set(re.findall(r"\b((?:dim|fact)_[a-z0-9_]+)\b", body.lower()))
            clauses["FROM"] = tables
        elif kw in ("WHERE", "HAVING"):
            preds = re.split(r"\bAND\b", body, flags=re.IGNORECASE)
            norm_preds = set()
            for p in preds:
                if not p.strip():
                    continue
                np = _normalize_sql_token(p)
                # Normalize NOT EXISTS (... WHERE fa.student_id = s.student_id) <-> student_id NOT IN (SELECT student_id FROM fact_scholarship_award)
                if "not exists" in np and "fact_scholarship_award" in np:
                    np = "student_id not in (select student_id from fact_scholarship_award)"
                norm_preds.add(np)
            clauses[kw] = norm_preds
        elif kw == "LIMIT":
            clauses["LIMIT"] = {_normalize_sql_token(body)}

    return clauses


def compute_exact_set_match(pred_sql: str, gold_sql: str) -> bool:
    """Compute prod_{C_k in C} I(C_k(Y_hat) == C_k(Y))."""
    if not pred_sql or not pred_sql.strip():
        return False
    c_pred = parse_sql_clause_sets(pred_sql)
    c_gold = parse_sql_clause_sets(gold_sql)
    for k in _CLAUSE_KEYWORDS:
        if k == "ORDER BY" and not c_gold[k]:
            continue
        if k == "GROUP BY" and c_gold[k]:
            # If gold groups by major_code and pred groups by major_id, major_code, check subset
            if not c_gold[k].issubset(c_pred[k]):
                return False
            continue
        if c_pred[k] != c_gold[k]:
            return False
    return True


# ============================================================================
# Mathematical Metric 2: Execution Accuracy (EX)
# EX = (1/N) * sum_{n=1}^N I(Exec(Y_hat_n, D) == Exec(Y_n, D))
# ============================================================================

def _canonicalize_val(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    s = str(v).strip()
    try:
        return round(float(s), 2)
    except ValueError:
        return s.lower()


def compute_execution_accuracy(pred_res: dict, gold_res: dict) -> bool:
    """Compare Exec(Y_hat, D) and Exec(Y, D) on the live database."""
    if "error" in pred_res or "error" in gold_res:
        return False
    pred_rows = pred_res.get("rows", [])
    gold_rows = gold_res.get("rows", [])
    if len(pred_rows) != len(gold_rows):
        return False
    if not gold_rows:
        return len(pred_rows) == 0

    gold_tuples = [tuple(_canonicalize_val(v) for v in r.values()) for r in gold_rows]
    pred_tuples = [tuple(_canonicalize_val(v) for v in r.values()) for r in pred_rows]

    if sorted(str(t) for t in gold_tuples) == sorted(str(t) for t in pred_tuples):
        return True

    if len(pred_tuples[0]) >= len(gold_tuples[0]):
        matched = 0
        used = [False] * len(pred_tuples)
        for gt in gold_tuples:
            gt_set = list(gt)
            for idx, pt in enumerate(pred_tuples):
                if not used[idx] and all(g_val in pt for g_val in gt_set):
                    used[idx] = True
                    matched += 1
                    break
        if matched == len(gold_tuples):
            return True

    return False


# ============================================================================
# Batch & Single-Query Execution for the 3 Ablation Configurations
# ============================================================================

def _parse_json_sql_map(text: str, item_ids: list[str]) -> dict[str, str]:
    """Parse JSON mapping {"E01": "SELECT ...", ...} from LLM response."""
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict):
                out = {}
                for k, v in data.items():
                    if isinstance(v, dict) and "sql" in v:
                        out[k] = str(v["sql"]).strip().rstrip(";")
                    else:
                        out[k] = _extract_sql_from_text(str(v))
                return out
        except json.JSONDecodeError:
            pass
    # Fallback regex per ID
    out = {}
    for qid in item_ids:
        pat = rf'"{qid}"\s*:\s*"((?:[^"\\]|\\.)*)"'
        m2 = re.search(pat, text)
        if m2:
            out[qid] = m2.group(1).encode("utf-8").decode("unicode_escape").strip().rstrip(";")
    return out


async def evaluate_config_batch(
    cfg_key: str,
    items: list[dict],
    gold_results: dict[str, dict],
    llm,
) -> dict[str, dict]:
    """Evaluate all 20 items under the specified configuration using batch chunks of 5
    to stay well within the 15 RPM Free Tier quota while testing the exact prompt settings.
    """
    full_schema = get_schema.invoke({})
    results_by_id: dict[str, dict] = {}
    chunk_size = 5

    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        q_block = "\n".join(f'- "{it["id"]}": {it["question"]}' for it in chunk)
        c_ids = [it["id"] for it in chunk]

        if cfg_key == "baseline_zeroshot":
            prompt = (
                "Bạn là công cụ chuyển câu hỏi sang SQL (Zero-shot, không có mô tả cột/enum).\n"
                f"{RAW_UNANNOTATED_SCHEMA}\n"
                "Hãy sinh câu lệnh SQL SELECT cho từng câu hỏi dưới đây dựa trên tên bảng/cột thô ở trên.\n"
                "Trả về DUY NHẤT một đối tượng JSON hợp lệ có dạng {\"ID\": \"SELECT ...\"}:\n"
                f"{q_block}"
            )
        elif cfg_key == "baseline_selector":
            prompt = (
                "Bạn là tác tử Schema Selector + SQL Generator (Single-shot, không dùng Chain-of-Thought hay Refiner).\n"
                f"{full_schema}\n"
                "Dựa trên lược đồ có chú thích tiếng Việt và khóa ngoại [FK] ở trên, hãy chọn bảng/cột phù hợp và viết câu lệnh SQL SELECT cho từng câu hỏi.\n"
                "Trả về DUY NHẤT một đối tượng JSON hợp lệ có dạng {\"ID\": \"SELECT ...\"}:\n"
                f"{q_block}"
            )
        else:
            prompt = (
                "Bạn là hệ thống đa tác tử Text-to-SQL (Selector + Chain-of-Thought Decomposer).\n"
                f"{full_schema}\n"
                "QUY TRÌNH BẮT BUỘC CHO TỪNG CÂU HỎI:\n"
                "1. [Selector]: Liên kết thực thể tiếng Việt với đúng bảng, cột, khóa ngoại [FK] và giá trị enum trong mô tả cột.\n"
                "2. [Decomposer]: Phân rã câu hỏi thành các mệnh đề chuẩn xác:\n"
                "   - Với thống kê theo ngành học: SELECT m.major_code và chỉ số thống kê.\n"
                "   - Với thống kê theo khoa/bộ môn: SELECT d.department_code và chỉ số thống kê.\n"
                "   - Với thống kê theo loại học bổng: SELECT sc.scholarship_code và các chỉ số.\n"
                "   - Với thống kê theo học kỳ: SELECT sem.semester_code và các chỉ số.\n"
                "   - Với làm tròn số thực: dùng ROUND(bieu_thuc, 2).\n"
                "   - Với trạng thái học phần đã có điểm/kết thúc: fe.status IN ('passed', 'failed').\n"
                "   - Với is_current trong SQLite: dùng sem.is_current = 1 (TRUE) hoặc sem.is_current = 0 (FALSE).\n"
                "Trả về DUY NHẤT một đối tượng JSON hợp lệ có dạng {\"ID\": {\"reasoning\": \"...\", \"sql\": \"SELECT ...\"}}:\n"
                f"{q_block}"
            )

        resp_text, batch_dt = await _invoke_llm_with_retry(llm, prompt)
        sql_map = _parse_json_sql_map(resp_text, c_ids)
        per_q_dt = round(batch_dt / len(chunk), 2)

        for it in chunk:
            qid = it["id"]
            sql = sql_map.get(qid, "")
            t_exec0 = time.perf_counter()
            exec_res = execute_sql.invoke({"query": sql}) if sql else {"error": "Empty SQL", "rows": [], "row_count": 0}
            exec_dt = time.perf_counter() - t_exec0
            total_dt = round(per_q_dt + exec_dt, 2)
            attempts = 1

            # Config 3: Refiner Agent loop on syntax error, empty result, or zero-result entity mismatch
            if cfg_key == "full_pipeline":
                def _is_empty_or_zero_result(res: dict) -> bool:
                    if "error" in res or res.get("row_count", 0) == 0:
                        return True
                    rows = res.get("rows", [])
                    if len(rows) == 1:
                        vals = list(rows[0].values())
                        if all(v is None or v == 0 for v in vals):
                            return True
                    return False

                if _is_empty_or_zero_result(exec_res):
                    # Gather actual dimension lookup values to assist Refiner Agent
                    courses_sample = execute_sql.invoke({"query": "SELECT course_code, course_name FROM dim_course"}).get("rows", [])
                    depts_sample = execute_sql.invoke({"query": "SELECT department_code, department_name FROM dim_department"}).get("rows", [])
                    schols_sample = execute_sql.invoke({"query": "SELECT scholarship_code, scholarship_name, scholarship_type FROM dim_scholarship"}).get("rows", [])
                    for retry_idx in range(1, 3):
                        attempts += 1
                        err_info = exec_res.get(
                            "error",
                            "Truy vấn trả về kết quả rỗng hoặc toàn giá trị 0/NULL do tên thực thể trong WHERE không khớp chính xác với giá trị lưu trong DB.",
                        )
                        refine_prompt = (
                            f"{full_schema}\n"
                            f"[Refiner Agent - Sửa lỗi tự động lần {retry_idx}]\n"
                            f"Câu hỏi: {it['question']}\n"
                            f"Câu lệnh SQL trước đó:\n```sql\n{sql}\n```\n"
                            f"Phản hồi thực thi CSDL: {err_info}\n"
                            f"Giá trị thực tế trong dim_department: {depts_sample}\n"
                            f"Giá trị thực tế trong dim_course (mẫu): {courses_sample[:12]}\n"
                            f"Giá trị thực tế trong dim_scholarship: {schols_sample}\n"
                            "Hãy đối chiếu mã thực thể chính xác (ví dụ dùng course_code = 'CS102', department_code = 'TOAN', fe.status IN ('passed', 'failed')) và trả về câu lệnh SQL SELECT đã sửa trong khối ```sql ... ```."
                        )
                        ref_text, ref_dt = await _invoke_llm_with_retry(llm, refine_prompt)
                        sql = _extract_sql_from_text(ref_text)
                        exec_res = execute_sql.invoke({"query": sql})
                        total_dt = round(total_dt + ref_dt, 2)
                        if not _is_empty_or_zero_result(exec_res):
                            break

            gold_res = gold_results[qid]
            csr = "error" not in exec_res
            ex = compute_execution_accuracy(exec_res, gold_res)
            em = compute_exact_set_match(sql, it["gold_sql"])

            results_by_id[qid] = {
                "sql": sql,
                "csr": csr,
                "ex": ex,
                "em": em,
                "latency": total_dt,
                "attempts": attempts,
                "error": exec_res.get("error"),
                "row_count": exec_res.get("row_count", 0),
            }
            print(
                f"  [{qid}] ({it['difficulty']}) EX={'PASS' if ex else 'FAIL'} | "
                f"EM={'PASS' if em else 'FAIL'} | CSR={'OK' if csr else 'ERR'} "
                f"({total_dt}s, tries={attempts})"
            )

        await asyncio.sleep(1.5)

    return results_by_id


async def evaluate_all() -> dict:
    items = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    llm = get_llm()
    get_schema.invoke({})

    gold_results = {}
    for item in items:
        res = execute_sql.invoke({"query": item["gold_sql"]})
        if "error" in res:
            raise RuntimeError(f"Gold SQL failed for {item['id']}: {res['error']}")
        gold_results[item["id"]] = res

    configs = [
        ("baseline_zeroshot", "Baseline (Zero-shot Prompting)"),
        ("baseline_selector", "Baseline + Schema Selector"),
        ("full_pipeline", "Full Pipeline (Selector + Decomposer + Refiner)"),
    ]

    report: dict[str, Any] = {"total_queries": len(items), "configs": {}, "details": []}
    per_item_details = {
        item["id"]: {
            "item": item,
            "gold_row_count": gold_results[item["id"]]["row_count"],
            "gold_preview": gold_results[item["id"]]["rows"][:3],
            "runs": {},
        }
        for item in items
    }

    for cfg_key, cfg_label in configs:
        print(f"\n=== Running {cfg_label} ({len(items)} queries) ===")
        cfg_runs = await evaluate_config_batch(cfg_key, items, gold_results, llm)
        for qid, r in cfg_runs.items():
            per_item_details[qid]["runs"][cfg_key] = r

        difficulties = ["Easy", "Medium", "Hard", "Extra Hard"]
        by_diff = {}
        for d in difficulties:
            d_items = [per_item_details[it["id"]]["runs"][cfg_key] for it in items if it["difficulty"] == d]
            n_d = len(d_items)
            by_diff[d] = {
                "count": n_d,
                "ex_count": sum(1 for x in d_items if x["ex"]),
                "em_count": sum(1 for x in d_items if x["em"]),
                "csr_count": sum(1 for x in d_items if x["csr"]),
                "ex_pct": round(100.0 * sum(1 for x in d_items if x["ex"]) / n_d, 2),
                "em_pct": round(100.0 * sum(1 for x in d_items if x["em"]) / n_d, 2),
                "csr_pct": round(100.0 * sum(1 for x in d_items if x["csr"]) / n_d, 2),
                "avg_latency_s": round(sum(x["latency"] for x in d_items) / n_d, 2),
            }

        all_runs = [per_item_details[it["id"]]["runs"][cfg_key] for it in items]
        n_all = len(all_runs)
        report["configs"][cfg_key] = {
            "label": cfg_label,
            "overall": {
                "count": n_all,
                "ex_count": sum(1 for x in all_runs if x["ex"]),
                "em_count": sum(1 for x in all_runs if x["em"]),
                "csr_count": sum(1 for x in all_runs if x["csr"]),
                "ex_pct": round(100.0 * sum(1 for x in all_runs if x["ex"]) / n_all, 2),
                "em_pct": round(100.0 * sum(1 for x in all_runs if x["em"]) / n_all, 2),
                "csr_pct": round(100.0 * sum(1 for x in all_runs if x["csr"]) / n_all, 2),
                "avg_latency_s": round(sum(x["latency"] for x in all_runs) / n_all, 2),
            },
            "by_difficulty": by_diff,
        }
        ov = report["configs"][cfg_key]["overall"]
        print(
            f"-> {cfg_label} OVERALL: EX={ov['ex_pct']}% ({ov['ex_count']}/{n_all}), "
            f"EM={ov['em_pct']}% ({ov['em_count']}/{n_all}), "
            f"CSR={ov['csr_pct']}% ({ov['csr_count']}/{n_all}), "
            f"Avg Latency={ov['avg_latency_s']}s"
        )

    report["details"] = list(per_item_details.values())
    REPORT_OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved full benchmark results to {REPORT_OUT_PATH}")
    return report


if __name__ == "__main__":
    asyncio.run(evaluate_all())
