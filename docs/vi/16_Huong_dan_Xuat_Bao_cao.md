# 17. Hướng dẫn Xuất Báo cáo

Report có thể gắn với experiment và analysis session, lưu format, content,
attachments và metadata. Export lưu source id, source type, format, path và
manifest.

Scientific notebook hỗ trợ Markdown và có thể attach report, experiment hoặc
figure:

```js
const notebook = laboratory.createNotebook({ projectId, title: 'Analysis notes' });
laboratory.appendNotebook(notebook.id, '## Observation\n\nReview pending.');
laboratory.attachNotebook(notebook.id, 'report', report.id, 'Primary report');
```

`createPublicationBundle()` tạo danh sách manuscript/report/figure/table/
supplementary/citation/reference và artifact manifest. Nó chỉ đóng gói các
reference do caller cung cấp, không tự viết lại manuscript hoặc evidence.
