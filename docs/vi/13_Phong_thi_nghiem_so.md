# 14. Phòng thí nghiệm số

Digital Laboratory là lớp quản lý metadata và workflow ở trên các module
phân tích hiện có:

```text
Laboratory
  ↓
Projects → Subjects → Trials → Experiments
                              ↓
                       Analysis Sessions
                              ↓
                    Reports → Exports
```

`DigitalLaboratory` nằm trong `web/digital_laboratory.js`. Nó nhận
`ExperimentWorkspace` hiện có làm backend dữ liệu chuẩn, không copy rollout
và không thay đổi loader hoặc simulation.

Laboratory hỗ trợ dashboard, browser, scientific notebook, publication bundle,
collaboration metadata và JSON persistence. Đây là product/workspace layer;
không phải một claim sinh học mới.
