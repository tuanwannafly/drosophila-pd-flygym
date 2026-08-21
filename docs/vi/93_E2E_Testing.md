# E2E Testing

Test nam trong `tests/e2e/` va dung Playwright Python. Chay bang:

```text
pytest -q --run-e2e tests/e2e
```

Playwright tests gom:

- app load
- dataset browser
- Viewer pose load
- Timeline seek
- playback controls
- Analysis tab
- Reports/Publication/Plugins tabs
- invalid JSON error handling

Viewer pose test chi chay khi `FLY_STUDIO_VIEWER_POSE` tro den artifact that.
Khi khong co artifact, pytest skip co ly do; day khong phai la pass gia bang
du lieu synthetic.

Moi test chup screenshot vao `docs/runtime/screenshots/` khi test ket thuc.
