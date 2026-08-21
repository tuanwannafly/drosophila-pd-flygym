# 8. Release Engineering

Release engineering là lớp kiểm soát repository, không phải lớp mô phỏng.
Mục tiêu là tạo metadata, kiểm tra sức khỏe, snapshot kiến trúc và report có
thể xem lại.

## Lệnh chính

```bash
PYTHONPATH=src python scripts/generate_release_report.py
```

Output mới nằm ở `docs/release_engineering/`:

- `release.json`: manifest máy đọc được;
- `release.md`: report Markdown;
- `release.html`: report HTML.

## Phạm vi report

Report ghi version, commit nguồn, compatibility matrix, số lượng module,
health summary, migration notes, plugin contract và trạng thái benchmark.
Report không regenerate evidence và không thay đổi các file đóng băng trong
`dist/`.

## Kiểm tra trước release

```bash
python -m compileall -q src scripts tests
PYTHONPATH=src pytest -q -rs -p no:cacheprovider
git diff --check
```

Các test cần FlyGym/MuJoCo vẫn được xác nhận trong Colab theo quy trình của
repository.
