# Hệ thống biểu đồ

`render_pd_figures` dùng matplotlib và chỉ vẽ các arrays có trong report. Các
nhóm biểu đồ gồm feature timeline, behavior timeline, feature importance, index
breakdown, correlation heatmap, feature profile, parallel profile và
distribution. Mỗi hình được xuất PNG/SVG khi dữ liệu tương ứng khả dụng.

Hình là sản phẩm trình bày của hậu xử lý. Việc có hình không đồng nghĩa với
việc endpoint đó đã được biological validation; dữ liệu thiếu sẽ được bỏ qua
thay vì thay bằng dữ liệu tổng hợp.
