# 5. Trạng thái dự án

## Nền tảng đã có

Repository hiện có các lớp behavior, gait, open field, progression, digital
twin, AI analysis, research campaign, experiment workspace, statistical
engine, integration hardening và verification/benchmark.

## Epic 11

Epic 11 bổ sung:

- plugin registry manifest-based với lifecycle rõ ràng;
- hook và capability contract;
- plugin context không lộ Workspace nội bộ;
- dependency checking và loader;
- ba plugin examples cho analysis, statistics và export;
- bộ tài liệu kỹ thuật tiếng Việt.

## Epic 12

Epic 12 bổ sung release engineering và developer experience:

- release manifest, version metadata, compatibility và migration notes;
- `ProjectHealth` cho health scan tĩnh;
- module/API/dependency/hook/architecture explorers;
- structured debug, timing, performance và diagnostic report;
- benchmark suite không tự chạy simulation;
- release report JSON/Markdown/HTML;
- tài liệu tiếng Việt cho release và developer workflow.

## Phần chưa nên suy diễn

Plugin platform không làm thay đổi simulation, controller, evidence JSON,
manuscript hoặc kết luận khoa học. Các plugin mới phải được kiểm thử như
software extension trước khi được dùng trong workflow nghiên cứu.
