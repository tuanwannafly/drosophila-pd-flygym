# 54. Kiem dinh dataset

`DatasetValidator` kiem tra manifest, metadata, file thieu, checksum, file
trung, trajectory, frame, timestamp, JSON hong va tinh day du cua goi.

`READY` chi co nghia la goi du lieu dat kiem tra phan mem/toan ven. No khong
phai la xac nhan sinh hoc, xac nhan Parkinson, hay ket luan khoa hoc.

Neu dataset chua co hoac khong hop le, pipeline phai giu trang thai
`WAITING_DATASET` hoac `FAILED` va khong tu sua file.
