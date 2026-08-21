# Rollout

`RolloutRecorder` đọc các getter công khai của FlyGym Simulation: body
positions/rotations, joint angles/velocities, actuator forces và ground contact
information khi có. Gia tốc khớp được tính từ hai mẫu vận tốc liên tiếp; đây là
phép dẫn xuất phần mềm, không phải một quan sát sinh học mới.

Mỗi frame giữ timestamp, step, thorax, COM khi MuJoCo cung cấp subtree COM,
orientation, body state, joint state, contact và actuator state. Camera và
simulation metadata được lưu ở cấp rollout.
