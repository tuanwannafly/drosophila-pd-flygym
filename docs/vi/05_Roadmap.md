# 6. Roadmap

Roadmap này chỉ ghi các hướng mở rộng phù hợp với kiến trúc hiện tại; không
tự tạo thêm kết luận khoa học.

1. Hoàn thiện contract test và ví dụ plugin trong Epic 11.
2. Duy trì release manifest và health scan cùng mỗi thay đổi lớn.
3. Bổ sung host adapters để expose các service read-only cần thiết cho plugin.
4. Đánh giá dependency graph và lifecycle trong môi trường browser/CI.
5. Bổ sung plugin documentation khi API capability mở rộng.
6. Chỉ sau khi review và test mới xem xét các extension cho workflow cụ thể.
7. Duy trì Digital Fly Model như lớp dữ liệu canonical cho các workflow V2.
8. Duy trì 3D motion engine như lớp hậu xử lý/hiển thị cho trajectory thật.

Mọi thay đổi phải giữ backward compatibility, chạy compileall/pytest/diff
check và cập nhật tài liệu tương ứng.

9. Duy trì Epic 16 như lớp computational phenotype analysis trên rollout
   thật; không suy diễn thành chẩn đoán hoặc validation sinh học.
10. Duy trì Epic 17 như lớp kiểm định agreement, reproducibility và hiệu năng
    trên dữ liệu tham chiếu đã import; không nâng cấp thành biological claim.
