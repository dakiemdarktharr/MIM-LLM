# Giảm xác nhận Drive lặp lại — 26/11/2026

Người dùng yêu cầu giữ kết nối Drive, không bắt xác nhận qua mỗi bước. Từ yêu
cầu này, notebook host giữ mount/VM giữa profiler và những driver đã được phép
chạy tiếp ngay sau kiểm tra tài nguyên. Không `flush_and_unmount()` hoặc
`runtime.unassign()` chỉ vì vừa xong một chunk/driver nếu còn bước hợp lệ trong
cùng phiên. V3 child vốn đã không tự unassign; quyết định kết thúc phiên thuộc
host. Đây là thay đổi orchestration, không thay model/data/tokenizer/budget.

Quy trình mỗi phiên:

1. Dùng lại đúng notebook riêng tư và VM/mount đang có. Chỉ mount khi chưa gắn;
   không force-remount. Kiểm đúng đường dẫn dự án và đọc/ghi probe riêng dự án.
2. Đọc CU/rate thực, giữ cap đã khai báo và chạy những bước đã được phép. Lưu
   checkpoint/metrics/config/hash lên Drive trong từng driver như trước.
3. Đọc lại cloud artifacts bằng connector mà không buộc tắt VM sau từng chunk.
   Khi persistence cần kiểm sau release, vẫn kiểm lại ở cuối phiên thật sự.
4. Nếu lỗi không thể tiếp tục an toàn, hoàn tất phần được phép, hoặc chạm cap:
   lưu bằng chứng, flush/unmount rồi trả VM. Không giữ GPU idle vô thời hạn chỉ
   để tránh xác thực. Giữ cap của resource annex hiện hành:16driver tối đa,
   1100s mỗi driver và16CU observed-drop; không tự mở
   mở test/B/C/Q1/tokenizer fit bằng thay đổi này.

Google [FAQ chính thức](https://research.google.com/colaboratory/faq.html)
(tra26/11/2026, mục “Why does Mount Drive sometimes insert code into the notebook?”)
nói thường phải cấp quyền khi kết nối runtime mới; tự mount về sau chỉ có trong
một số trường hợp notebook vượt các kiểm tra của Google. VM có lifetime hữu
hạn và có thể bị xóa khi idle. Vì vậy không thể hứa một mount vĩnh viễn hay bật
một tùy chọn để bỏ mọi Google verification. Giữ VM giữa công việc liên tiếp là
phương án giảm số lần xác nhận; không bảo đảm không bao giờ cần xác thực lại.

Không lưu mật khẩu/OTP/refresh token vào GitHub/notebook, đổi quyền chia sẻ hay
dùng keepalive giả. Drive connector đã hoạt động và đọc artifacts độc lập;
quyền connector không đồng nghĩa filesystem mount tự tồn tại trong VM mới.

Lịch sử: v1/v2/v3 host cũ trả VM sau từng driver để giảm thời gian idle; giữ
nguyên receipt/log nguồn cũ. Ô profiler hiện tại giữ mount khi thành công và
trả VM khi lỗi; chưa gọi bước đó là hoàn tất trước khi có receipt thực.

## Cập nhật 27/11/2026

Drive connector vẫn đọc được archive lượt3 mà không yêu cầu người dùng cấp
quyền lại. Sau lần tạm dừng, UI notebook báo runtime đã ngắt và0active sessions;
mount filesystem cũ không còn được xem là đang hoạt động. Không dùng receipt
mount lịch sử làm bằng chứng cho VM mới. Đã thử nối lại L4, nhưng UI giữ ở
Allocating runtime; sau một lần làm mới đã chọn T4 được phép. T4 được cấp
1active session/rate1,87CUh, kernel vẫn đang Connecting ở quan sát này.
Yêu cầu chạy ô mount12 đã gửi đúng một lần; chưa xác nhận mount mới thành công.

Người dùng đã cho phép dùng lại đúng tài khoản và phạm vi Drive cho dự án.
Không hỏi lại cùng một quyền. Chỉ chuyển thao tác cho người dùng nếu Google
bắt một bước xác thực cá nhân không thể thực hiện thay. Không tạo/service
account, lưu credential hoặc mở public dữ liệu để né xác thực.

Sửa câu cap8driver còn sót ở phần quy trình: annex được ghi trước lượt2 đã
nâng thành16; thay đổi này chỉ sửa tài liệu, không tăng ngân sách hiện hành.

### Xác nhận bằng công việc thật — 27/11/2026

Mount đã hoạt động và được giữ qua các lượt4–10; ghi chép kernel còn Connecting
ở trên là lịch sử. Connector đã đọc lại ledger, receipt và các phần ZIP lượt9
độc lập, không hỏi grant mới. Giới hạn một file256MiB được xử lý bằng các phần
100MiB có hash rồi ghép đúng byte, không thay quyền chia sẻ hoặc thêm credential.
Hiện không có bước xác thực cá nhân đang chờ. Giữ mount giữa công việc hợp lệ
theo chính sách; không hứa filesystem mount tồn tại sau khi Google xóa VM.
