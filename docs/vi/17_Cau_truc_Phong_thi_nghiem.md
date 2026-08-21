# 18. Cấu trúc Phòng thí nghiệm

```text
DigitalLaboratory
├── ExperimentWorkspace (source of truth cho rollout đã chuẩn hóa)
├── Project store
├── Subject store
├── Trial store
├── Experiment store
├── AnalysisSession store
├── Report store
├── Export store
├── Notebook store
├── Dashboard / Browser view-model
└── Publication bundle builder
```

`web/app.js` expose `this.laboratory` nhưng không thay thế các panel/workspace
hiện có. Không có framework UI mới; UI tương lai có thể đọc model này qua API
được định nghĩa.

Collaboration metadata gồm author, institution, ORCID, dataset, license và
citation khi caller cung cấp. Metadata thiếu không được tự suy đoán.
