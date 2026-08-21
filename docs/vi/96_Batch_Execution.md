# Thực thi theo lô

Chạy campaign theo thứ tự khai báo bằng:

```powershell
python scripts/run_campaign.py batch --campaign experimental_campaign_01_healthy_baseline
```

Runtime chỉ chạy các dataset có manifest hợp lệ và rollout thật. Job chưa có
dataset giữ trạng thái `WAITING`; job lỗi có thể được thử lại ở lần chạy sau.
