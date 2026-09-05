from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from agent.llm import get_llm
from agent.tools.sql_tools import execute_sql, get_schema

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


def get_sql_agent() -> CompiledStateGraph:
    global _agent
    if _agent is None:
        _agent = create_react_agent(
            model=get_llm(),
            tools=[get_schema, execute_sql],
            prompt=_SQL_SYSTEM_PROMPT,
        )
    return _agent
