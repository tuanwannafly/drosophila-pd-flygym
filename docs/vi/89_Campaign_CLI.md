# Campaign CLI

CLI nằm tại `scripts/research_campaign_cli.py`.

```bash
python scripts/research_campaign_cli.py --help
python scripts/research_campaign_cli.py create --name demo --state campaign.json
```

Các lệnh gồm `create`, `run`, `pause`, `resume`, `cancel`, `status`, `history`,
`bundle`, `validate` và `report`. Lệnh `run` không có executor chỉ chuẩn bị
trạng thái; không tự chạy simulation.
