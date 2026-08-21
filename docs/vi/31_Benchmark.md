# Benchmark

`benchmark_operations` và `benchmark_scalability` đo CPU time, peak memory,
output hash và các cache metrics do caller cung cấp. Framework không tự chạy
simulation và không tự tạo workload khoa học.

Benchmark chỉ có ý nghĩa cho operation và dataset mà người dùng truyền vào.
Một report thiếu operation sẽ ghi `available=false`, không thay bằng số liệu
ước lượng.
