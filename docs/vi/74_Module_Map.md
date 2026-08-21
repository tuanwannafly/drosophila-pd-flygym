# Ban do module

| Khu vuc | Vi tri | Trang thai |
| --- | --- | --- |
| Scientific pipeline | `src/drosophila_pd/experiments`, `metrics`, `analysis` | Frozen/stable |
| Validation | `src/drosophila_pd/scientific_validation` | Stable |
| Rollout adapter | `src/drosophila_pd/dataset_adapter`, `flygym_adapter` | Additive |
| Workflow | `research_execution`, `research_campaign`, `research_kernel` | Additive orchestration |
| Fly Studio | `src/drosophila_pd/flystudio`, `web/` | Additive presentation |
| Viewer preparation | `web/viewer/` | Skeleton, not wired |
| Documentation | `docs/`, `docs/vi/` | Indexed |

Ten trung lap khong dong nghia voi code trung lap: moi module co boundary
khac nhau. Audit phan loai cac truong hop chua du bang chung de gop.
