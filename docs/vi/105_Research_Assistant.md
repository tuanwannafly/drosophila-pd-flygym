# Research Assistant

## Pham vi

`ResearchAssistant` la lop orchestration chi doc cac artifact tinh toan da co:

- dataset
- analysis
- statistics
- validation
- reports

Lop nay khong chay simulation, khong goi mo hinh AI noi bo, khong tao metric moi va khong dua ra ket luan sinh hoc.

## Dau ra

Co the sinh `assistant_report.json` va `assistant_report.md`, gom:

- tom tat artifact
- findings tu cac artifact da cung cap
- canh bao thieu du lieu hoac gia tri khong huu han
- khuyen nghi workflow co the kiem tra
- ghi chu chuan bi publication

## Su dung

```python
from drosophila_pd.research_assistant import ResearchAssistant

assistant = ResearchAssistant(artifact_root="results/study")
report = assistant.generate()
assistant.write("results/study/assistant", report)
```

Giai thich metric, chart va validation la mo ta dinh danh, khong thay the phan tich hoac validation goc.
