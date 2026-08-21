# Web Player

Web Player gồm viewport Three.js và timeline điều khiển tối thiểu:

- Play, Pause, Stop
- seek theo frame
- tốc độ 0.25x đến 4x
- Loop
- Reset view

Các thao tác camera OrbitControls hỗ trợ orbit, pan và zoom. Player chỉ đọc
pose/rollout đã nạp; không ghi ngược vào dataset hay scientific evidence.

Nếu trình duyệt không hỗ trợ WebGL, viewer báo lỗi thân thiện trong viewport.
Canvas viewer hiện có vẫn là đường hiển thị cho scene JSON thông thường.
