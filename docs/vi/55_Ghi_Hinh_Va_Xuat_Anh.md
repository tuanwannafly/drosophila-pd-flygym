# 55. Ghi hình và xuất ảnh

Toolbar hỗ trợ snapshot PNG và SVG của viewport. Session Recorder tiếp tục lưu
thao tác workspace dưới dạng JSON.

Video có thể dùng `canvas.captureStream()` và `MediaRecorder` nếu trình duyệt
cho phép; GIF không có encoder tích hợp và được báo là chưa khả dụng khi môi
trường không cung cấp encoder. Không có file trung gian nào được thêm vào
repository.
