# 9. Hướng dẫn Developer

## Bắt đầu

1. Đọc `AGENTS.md` và `PROJECT_CONTEXT.md`.
2. Kiểm tra branch và working tree.
3. Xác định module owner và public API liên quan.
4. Chỉ sửa phạm vi cần thiết.
5. Chạy compileall, pytest và diff check.

## Python module mới

Đặt reusable logic trong `src/drosophila_pd/`, thêm type hints, docstring và
test tương ứng trong `tests/`. Không import module nghiên cứu chỉ để chạy
health scan; tooling nên dùng static inspection khi có thể.

## Web module mới

Web modules là ESM trong `web/`. Giữ Workspace làm source of truth, không tạo
state trùng lặp, không parse lại input nếu module hiện có đã chuẩn hóa dữ
liệu. Plugin dùng `PluginContext` thay vì truy cập Workspace trực tiếp.

## Review

Tự kiểm tra dead code, duplicate logic, naming, coupling, backward
compatibility và scientific boundary trước khi commit.
