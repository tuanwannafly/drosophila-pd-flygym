# Epic 13 — Digital Parkinson Laboratory

## Mục tiêu

Epic 13 tạo lớp product/workspace cho quản lý project và analysis. Đây không
phải framework simulation mới, không thêm Analytics/Statistics/Parkinson
Engine và không thay đổi evidence.

## Workflow

```text
Laboratory
  → Project
  → Subject
  → Trial
  → Experiment
  → Analysis Session
  → Report
  → Export
```

`DigitalLaboratory` tái sử dụng `ExperimentWorkspace`, `PluginPlatform` và
các report/export API hiện có. Model hỗ trợ dashboard counts, browser filter/
search/sort/group/recent/favorite, Markdown notebook, publication bundle,
collaboration metadata và persistence.

## Files

- `web/digital_laboratory.js`
- `web/app.js` được bổ sung property `laboratory`;
- `tests/test_digital_laboratory_contract.py`;
- tài liệu `docs/vi/13_*` đến `17_*`.

## Ranh giới khoa học

Laboratory lưu metadata và liên kết artifact do caller cung cấp. Nó không
chạy simulation, không tạo evidence, không diễn giải Parkinson và không sửa
manuscript, notebook lịch sử hoặc release artifact.

## Validation

```bash
python -m compileall -q src scripts tests
PYTHONPATH=src pytest -q -rs -p no:cacheprovider
git diff --check
```

Manual smoke test cần xác nhận hierarchy, dashboard, browser, notebook
attachments, publication bundle và JSON restore trong browser runtime.
