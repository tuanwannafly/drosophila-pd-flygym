# Hướng dẫn lập trình

Logic dùng lại đặt trong `src/drosophila_pd/`; CLI chỉ điều phối. Trước khi
đổi module, đọc package `__init__.py`, test và tài liệu liên quan. Không sửa
evidence, manuscript, notebook hoặc release artifact nếu chưa được ủy quyền.

Kiểm tra tối thiểu:

```bash
python -m compileall -q src scripts tests
pytest -q -rs -p no:cacheprovider
git diff --check
```
