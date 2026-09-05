# Python / Sonar Coding Rules

Checklist ngắn gọn để dùng khi code hoặc review PR.

| # | Rule | Ý chính |
|---|---|---|
| 1 | Tên biến/function rõ nghĩa | Không dùng `x`, `tmp`, `data1` nếu có thể đặt rõ hơn |
| 2 | 1 biến = 1 ý nghĩa | Không dùng một biến lúc là `list`, lúc đổi thành `int` hoặc `str` |
| 3 | 1 function = 1 responsibility | Không vừa validate, save DB, gửi mail, generate report trong cùng function |
| 4 | Function không quá dài | Khoảng `< 40–50 dòng`; dài hơn thì cân nhắc tách |
| 5 | Không nesting quá sâu | `if/for/while` nên tối đa khoảng `2–3 level` |
| 6 | Không quá nhiều `if/elif` | Nhiều nhánh cố định thì dùng `match-case` hoặc dispatch table |
| 7 | Case trùng phải gom | Nhiều case cùng xử lý thì merge lại |
| 8 | Không nested `for` quá nhiều | `3+ vòng lặp lồng nhau` là dấu hiệu cần xem lại |
| 9 | Cognitive Complexity thấp | Sonar thường nên giữ function khoảng `<= 15` |
| 10 | Dùng type cụ thể | Hạn chế `Any`; ưu tiên `str`, `int`, `User`, `list[User]`... |
| 11 | `None` phải khai báo đúng type | Dùng `User \| None`, không tự động đổi `None` thành `"None"` |
| 12 | Import ở đầu file | Standard library → third-party → local project |
| 13 | Không `import *` | Import rõ những gì cần dùng |
| 14 | Không duplicate code | Logic giống và cùng ý nghĩa business thì tách thành function |
| 15 | Không magic number/string | Dùng constant hoặc Enum |
| 16 | Không hard-code config/secret | URL, password, API key → env/config/secret manager |
| 17 | `try/except` phải xử lý hoặc ném lỗi | Không được `except: pass` |
| 18 | Catch đúng exception | Ưu tiên `ValueError`, `TimeoutError`... thay vì bắt `Exception` bừa bãi |
| 19 | Không nuốt lỗi | Log + `raise`, hoặc chuyển sang domain exception phù hợp |
| 20 | Dùng guard clause | Return/raise sớm để tránh `if` lồng nhau |
| 21 | Không Boolean comparison dư thừa | `if is_active:` thay vì `if is_active == True:` |
| 22 | Không sửa list khi đang loop trực tiếp | Tránh `remove()` collection đang iterate |
| 23 | Không mutable default argument | Không dùng `def f(items=[])` |
| 24 | Không unused import/variable/code | Xóa dead code và code comment cũ |
| 25 | Không `print()` trong production | Dùng `logger` |
| 26 | Comment giải thích WHY | Không comment lại đúng thứ code đang làm |
| 27 | Input phải validate | Validate sớm ở API/service boundary |
| 28 | Không trả nhiều type linh tinh | Tránh `User \| str \| bool`; dùng type/result rõ ràng |
| 29 | Không side effect bất ngờ | Function tên `calculate_*` không nên âm thầm update DB |
| 30 | Ưu tiên code đơn giản | KISS, DRY, YAGNI; không over-engineering |

## Rule cho nhiều `if/elif`

Không nên:

```python
if action == "create":
    create()
elif action == "update":
    update()
elif action == "delete":
    delete()
```

Có thể dùng `match-case`:

```python
match action:
    case "create":
        create()
    case "update":
        update()
    case "delete":
        delete()
    case _:
        raise ValueError("Unsupported action")
```

Nếu nhiều case dùng chung logic thì gom:

```python
match status:
    case "pending" | "processing":
        wait_for_completion()
    case "done":
        complete()
```

Hoặc dùng dispatch table:

```python
handlers = {
    "create": create,
    "update": update,
    "delete": delete,
}

handler = handlers.get(action)

if handler is None:
    raise ValueError("Unsupported action")

handler()
```

## Rule cho `try/except`

Không được nuốt lỗi:

```python
try:
    process()
except Exception:
    pass
```

Nên xử lý và ném lại lỗi:

```python
try:
    process()
except ValueError:
    logger.exception("Invalid data")
    raise
```

Hoặc chuyển sang domain exception:

```python
try:
    repository.get_user(user_id)
except DatabaseError as exc:
    raise UserRepositoryError(user_id) from exc
```

## Công thức nhớ nhanh

**Tên rõ + type rõ + function nhỏ + ít nesting + ít duplication + lỗi không bị nuốt + logic đơn giản + dễ test.**
