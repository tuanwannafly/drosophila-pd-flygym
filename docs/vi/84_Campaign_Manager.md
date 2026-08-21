# Campaign Manager

`CampaignManager` quản lý nhiều campaign trong bộ nhớ hoặc JSON. Mỗi campaign
có UUID, metadata, danh sách experiment, trạng thái, lịch sử và thư mục output.
Experiment chỉ nhận một executor do caller cung cấp.
