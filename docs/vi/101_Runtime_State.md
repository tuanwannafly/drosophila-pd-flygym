# Runtime State

State hiện tại gồm frame, pose, velocity, acceleration, joint, COM,
orientation, cờ nội suy và các frame nguồn. Runtime còn giữ rolling history,
frame cache, trajectory cache và prediction buffer.

State này là trạng thái phần mềm của Digital Twin. Nó không phải measurement
mới và không phải kết luận sinh học.
