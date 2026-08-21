# 64. Huong dan van hanh

1. Chon mot template trong `configs/campaign_templates/`.
2. Tao campaign bang `CampaignManager.create_from_template`.
3. Kiem tra dataset gate; dataset thieu phai giu `WAITING_DATASET`.
4. Khi dataset da duoc phe duyet, chuyen sang `READY` va xep hang bang
   `CampaignScheduler`.
5. Xuat dashboard va publication plan bang cac API explicit.
6. Chi mot he thong execution da duoc phe duyet moi duoc xu ly experiment.

Khong chay simulation trong buoc chuan bi. `READY` chi la trang thai san sang
ve mat orchestration, khong phai ket luan sinh hoc.
