# Browser Runtime

Fly Studio Web duoc phuc vu truc tiep bang Python `http.server`; khong can
Node.js. Lenh chay:

```text
python scripts/run_web_demo.py --port 8000
```

E2E tests dung Playwright khi cai optional dependency:

```text
pip install -e ".[e2e]"
playwright install chromium
pytest -q --run-e2e tests/e2e
```

Test Viewer khong tao pose fixture. Hay dat `FLY_STUDIO_VIEWER_POSE` den mot
`viewer_pose.json` that da duoc sinh boi Viewer Pose Export Pipeline.

## Runtime errors

Test thu thap `pageerror`, loi console va dialog loi. JSON loi phai hien thong
bao than thien va khong lam mat Workspace truoc do.
