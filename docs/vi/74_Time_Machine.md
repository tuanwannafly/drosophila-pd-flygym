# 74. Time Machine

Time Machine lưu snapshot bất biến, restore state, tạo branch, đặt bookmark và
so sánh hai snapshot. Restore chỉ thay đổi trạng thái quản lý trong phiên; nó
không sửa rollout gốc hoặc evidence.

CLI kiểm tra platform:

```bash
python scripts/digital_twin_platform_cli.py validate --input platform.json
```
