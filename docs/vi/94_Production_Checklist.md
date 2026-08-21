# Production Checklist

- [ ] Cai `pip install -e ".[e2e]"`.
- [ ] Cai browser bang `playwright install chromium`.
- [ ] Chay `python scripts/run_web_demo.py`.
- [ ] Dat `FLY_STUDIO_VIEWER_POSE` den pose artifact that.
- [ ] Chay `pytest -q tests/e2e`.
- [ ] Kiem tra khong co page error hoac unhandled rejection.
- [ ] Luu screenshots va runtime report.
- [ ] Chay compileall, full pytest va git diff check.
- [ ] Xac nhan khong co thay doi FlyGym, scientific pipeline, exporter,
  evidence, dataset hoac release artifact.
