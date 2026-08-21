# Digital Twin Runtime

`DigitalTwinRuntime` là lớp stateful cho DigitalFly3D đã được import hoặc cho
stream frame đã parse. Runtime quản lý pose, thời gian, playback, cache và
event đồng bộ. Runtime không đọc file, không chạy FlyGym và không thay đổi
pipeline khoa học.

Mọi frame do stream cung cấp vẫn giữ nguồn gốc. Frame nội suy được đánh dấu
`interpolated` và chỉ xuất hiện khi có hai frame thật bao quanh vị trí cần tìm.
