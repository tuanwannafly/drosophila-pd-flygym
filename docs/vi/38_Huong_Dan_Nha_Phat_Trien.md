# Hướng dẫn nhà phát triển

Giữ workflow theo hướng một chiều: import → normalize/validate → Digital Fly
→ analysis → report/export. Tái sử dụng service hiện có trong `web/` và Python
package; không tạo bản sao logic khoa học trong dashboard. Mọi API mới phải
giữ backward compatibility và có contract test.
