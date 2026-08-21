# Quan ly dataset

`DatasetManager` quan ly cac file rollout va ket qua da ton tai. Khoi tao
layout chi tao thu muc metadata:

```text
datasets/<dataset_id>/
  healthy/ pd/ candidate/ benchmark/ validation/ metadata/
  manifest.json
  checksum.json
```

Khong co sample nao duoc sinh khi goi `initialize()`. Chi file hien huu moi
duoc dang ky bang `register_file()`. Manifest luu vai tro, duong dan, kich
thuoc va SHA-256. `verify()` phat hien file thieu, file bi sua va record trung.

Dataset lon va raw rollout khong nen commit mac dinh. Hay luu manifest nho,
provenance va checksum khi artifact duoc curat ro rang.
