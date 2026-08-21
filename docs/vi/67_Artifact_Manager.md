# 67. Artifact Manager

Artifact Manager tạo layout deterministic cho figures, videos, reports,
tables, JSON, CSV, logs và datasets. File phải do caller cung cấp; manager
chỉ register, copy theo yêu cầu, inventory và ghi SHA-256 manifest.

Integrity verification so sánh file hiện tại với manifest đã ghi.
