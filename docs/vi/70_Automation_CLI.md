# 70. Automation CLI

CLI nằm tại `scripts/research_automation_cli.py`:

```bash
python scripts/research_automation_cli.py health-check
python scripts/research_automation_cli.py generate-manifest --output automation_manifest.json
python scripts/research_automation_cli.py benchmark
python scripts/research_automation_cli.py create-bundle --output bundle/
python scripts/research_automation_cli.py export-publication --output publication/
```

Các lệnh chỉ quản lý metadata, artifact và validation software. Không lệnh nào
tạo rollout hoặc tự gọi simulation.
