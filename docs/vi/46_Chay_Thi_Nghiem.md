# Chay thi nghiem thuc te

Package `drosophila_pd.experiment` dieu phoi mot experiment thong qua cac stage
duoc truyen vao tu pipeline that. Cac stage thu tu la rollout, Digital Fly,
motion 3D, analysis, computational PD, scientific validation va publication
export.

Runner khong tu import FlyGym, khong tao rollout mac dinh va khong tao du lieu
khoa hoc gia. Ung dung goi phai cung cap handler cho tung stage. Moi handler
nhan context chua job, config, duong dan artifact va ket qua cac stage truoc.

Vi du lenh:

```bash
python scripts/run_experiment.py \
  --config configs/v2/experiment/job.json \
  --output datasets/experiments \
  --handler rollout=my_pipeline:run_rollout \
  --handler digital_fly=my_pipeline:build_digital_fly \
  --handler motion_3d=my_pipeline:run_motion \
  --handler analysis=my_pipeline:run_analysis \
  --handler computational_pd=my_pipeline:run_pd_analysis \
  --handler scientific_validation=my_pipeline:validate \
  --handler publication_export=my_pipeline:export_publication
```

Lenh tren chi la mau orchestration. Handler phai ton tai trong moi truong
chay va tu chiu trach nhiem ve FlyGym/MuJoCo. Colab la moi truong thuc thi;
GitHub va manifest la nguon provenance.
