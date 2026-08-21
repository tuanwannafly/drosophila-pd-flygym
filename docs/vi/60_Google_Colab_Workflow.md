# Google Colab Workflow

`notebooks/colab/` là chuỗi notebook độc lập cho một môi trường Colab mới.
Mỗi notebook tự tìm hoặc clone repository theo đường dẫn tương đối, cài
package và xử lý lỗi với thông báo rõ ràng.

Chuỗi gồm setup, API inspection, tạo fly, simulation hữu hạn, ghi rollout,
tạo Healthy_001, kiểm tra dataset, chạy pipeline, trực quan hóa, validation
và workflow end-to-end.

Colab là môi trường chạy simulation thật. CI chỉ kiểm tra cấu trúc notebook,
không chạy FlyGym/MuJoCo.
