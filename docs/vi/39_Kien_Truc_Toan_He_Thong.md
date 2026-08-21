# Kiến trúc toàn hệ thống

Rollout Loader cung cấp input cho Workspace, Digital Fly và 3D Motion Engine.
Analysis, Computational PD và Scientific Validation chỉ đọc dữ liệu đã import.
Dashboard gọi các service này để hiển thị; Release Candidate Builder chỉ lập
inventory và health report. Không module release nào sửa simulation hoặc evidence.
