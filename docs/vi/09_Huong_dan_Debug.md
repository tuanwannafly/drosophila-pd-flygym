# 10. Hướng dẫn Debug

Module `drosophila_pd.debug_utils` cung cấp các primitive opt-in:

- `StructuredEventLog`: event có level, timestamp và payload;
- `DebugLogger`: facade `debug/info/warning/error`;
- `TimingTrace`: context manager đo elapsed time;
- `PerformanceTrace`: đo thời gian và memory trace khi cần;
- `DiagnosticReport`: gom event, health và benchmark.

Ví dụ:

```python
from drosophila_pd.debug_utils import DebugLogger, StructuredEventLog, TimingTrace

events = StructuredEventLog()
logger = DebugLogger(events)
logger.info("workflow.start", component="release")
with TimingTrace("static_scan", events):
    pass
```

Debug utility không tự chạy simulation và không nên ghi raw data lớn vào Git.
Payload cần có cấu trúc JSON-friendly, không chứa secret hoặc thông tin môi
trường nhạy cảm.
