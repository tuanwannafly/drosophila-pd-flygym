# Dữ liệu tham chiếu

`ReferenceDatasetManager` quản lý các role `Healthy`, `PD`, `Candidate`,
`Control`, `Validation Set` và `Benchmark Set`. Role là nhãn tổ chức dữ liệu;
không phải kết luận sinh học.

Manifest JSON trỏ tới rollout JSON/NPZ đã tồn tại và lưu metadata, path và
SHA-256. Manager chỉ index/load dữ liệu được cung cấp. File không tồn tại,
format không hỗ trợ hoặc rollout không hợp lệ sẽ báo lỗi rõ ràng.
