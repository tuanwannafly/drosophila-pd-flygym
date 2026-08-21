# 53. Import dataset

Nguon import duoc ho tro:

- thu muc dataset;
- file ZIP;
- mot rollout;
- nhieu rollout.

Vi du Python:

```python
from drosophila_pd.dataset_registry import DatasetRegistry

registry = DatasetRegistry("datasets")
registry.initialize_layout()
result = registry.import_directory("/duong/dan/dataset", dataset_type="healthy")
print(result.status)
```

Duong dan nguon phai tro den du lieu that. Registry copy vao thu muc dich da
chi dinh, tao manifest va checksum, sau do tra ket qua health.
