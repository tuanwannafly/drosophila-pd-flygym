# 16. Hướng dẫn Phân tích

Analysis session lưu metadata của một lần phân tích:

- history;
- parameters;
- feature selection;
- statistics;
- plugin state;
- timeline.

Ví dụ:

```js
const session = laboratory.createAnalysisSession({
  experimentId,
  featureSelection: ['speed', 'heading'],
  parameters: { mode: 'descriptive' },
});
laboratory.recordAnalysis(session.id, { status: 'reviewed' });
```

Model này không tự chạy analysis. Analysis thật vẫn do pipeline hiện có thực
hiện; Laboratory chỉ lưu provenance/session state và liên kết kết quả.
