# Frame Stream

Frame được thêm bằng `append_frame(frame)` hoặc `append_frames(frames)`. Frame
có `frame_index` sẽ được ghi theo index đó; nếu thiếu, runtime cấp index tuần
tự cho stream mới. Thay đổi stream sẽ xóa các cache dẫn xuất.

`seek(frame)` đọc frame thật nếu có. Khi frame đích nằm giữa hai frame thật,
runtime nội suy giá trị số và quaternion rồi ghi rõ `sourceFrames`. Ngoài biên,
runtime chỉ dùng frame biên có thật, không ngoại suy.
