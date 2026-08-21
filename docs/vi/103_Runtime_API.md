# Runtime API

Các API chính:

- `append_frame`, `update`, `seek`, `reset`, `clear`;
- `getState`, `getFrame`, `getTrajectory`;
- `play`, `pause`, `resume`, `stop`, `tick`;
- `setSpeed`, `setLoop`, `setReverse`;
- `on`, `onChange`, `off` cho đồng bộ Timeline, Charts, Inspector,
  Selection và Viewer qua callback bên ngoài.

Runtime không import các module giao diện. Bên tích hợp đăng ký listener trên
`frame_changed`, `playback_changed` và `reset` để đồng bộ các phần cần thiết.
