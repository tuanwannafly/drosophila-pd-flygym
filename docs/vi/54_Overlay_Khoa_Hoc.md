# 54. Overlay khoa học

Các overlay có thể bật/tắt độc lập:

- trajectory và skeleton;
- joint axes, COM và body labels;
- velocity/angular vectors khi trajectory tương ứng tồn tại;
- ground contacts khi rollout có channel contact.

Velocity là sai phân hiển thị từ hai mẫu trajectory liền kề. Contact marker chỉ
được vẽ khi channel contact/ground_contact có giá trị. Renderer không suy đoán
contact, không thêm dữ liệu và không biến overlay thành bằng chứng sinh học.
