# Hướng dẫn chấm khả năng viết của foundation — 27/11/2026

Đây là hướng dẫn bổ sung **trước khi sinh panel subword**. Chưa có nhãn người
thật. Giữ nguyên 34 prompt, cách giải mã và rule
[`foundation_writing_rule.json`](../configs/q3a/foundation_writing_rule.json);
không thay ngưỡng hoặc sửa đoạn sinh sau khi xem kết quả.

## Cách làm

Mở `packet.jsonl`, `GUIDE.md` và `reader-author.csv` trong thư mục phiếu sẽ
được tạo từ output thật. Để `PRIVATE-key.jsonl` đóng tới khi đã lưu tất cả
đánh giá. Thứ tự đã xáo trộn, tên model bị ẩn; người chấm vẫn là tác giả,
không phải người đánh giá độc lập. Không suy đoán model để cho điểm.

Đọc cả prompt và toàn bộ continuation của từng item. Giữ cả đoạn trống,
lặp hoặc bị cắt ở giới hạn token. Không tự viết nốt câu, sửa lỗi hoặc chọn
một lần sinh khác. Mỗi dòng CSV giữ nguyên `item_id`; dùng cùng một
`rater_id` thật, ổn định cho toàn bộ lượt chấm. Ghi thời gian thực đọc và
chấm item vào `elapsed_seconds` theo giây, số dương; không tự điền một thời
gian ước lượng cho tất cả các dòng. Có thể nghỉ giữa các item.

## Ý nghĩa các cột

| Cột | Cách chấm |
|---|---|
| `format_3_to_5` | 1 nếu continuation gồm 3–5 câu có thể đọc hiểu; 0 nếu không. Đếm câu theo ngữ nghĩa, không đếm máy móc từng dấu chấm trong viết tắt hoặc lời thoại. Câu bị cắt không tính là câu hoàn chỉnh. |
| `fluency_1_to_5` | Độ tự nhiên và dễ hiểu của tiếng Anh, theo các mốc dưới đây. Đánh riêng với đúng/sai logic. |
| `follows_prefix` | 1 nếu viết tiếp phù hợp với prefix và thực hiện yêu cầu; 0 nếu bỏ qua, lạc sang chuyện khác hoặc không thực hiện. Với prompt vô điều kiện yêu cầu đúng ba câu, chỉ cho 1 khi đáp ứng cả yêu cầu đó. |
| `new_event` | 1 nếu có ít nhất một hành động hoặc thay đổi trạng thái mới, hiểu được; 0 nếu chỉ lặp prompt hoặc tả cảnh chung chung. Không bắt buộc một hành động cụ thể chưa có trong prompt. |
| `self_consistent` | 1 nếu các khẳng định hiểu được không mâu thuẫn với prompt và các khẳng định trước đó của chính đoạn sinh; 0 nếu có mâu thuẫn. Không phạt việc thêm chi tiết hợp lệ chỉ vì nó không có trong một đáp án mẫu. |
| `unclear` | 1 nếu mơ hồ/khó hiểu đến mức không thể quyết định đáng tin cậy về sự kiện hoặc tính nhất quán; 0 nếu đánh giá được. Không đoán ý tác giả để cứu câu khó hiểu. |
| `evidence` | Trích một cụm ngắn từ output và giải thích quyết định, hoặc ghi rõ phần bị thiếu. Có thể viết tiếng Việt. Ghi cả trường hợp mơ hồ; không chỉ ghi “good” hoặc “bad”. |

Mốc độ trôi chảy: **1** = phần lớn không hiểu được; **2** = thường xuyên
đứt nghĩa hoặc lỗi nghiêm trọng, phải đoán/sửa nhiều để hiểu; **3** = phần
lớn hiểu được và có mạch đọc, vẫn có lỗi hoặc cách dùng từ thiếu tự nhiên;
**4** = rõ ràng, tự nhiên, chỉ có lỗi nhỏ; **5** = nhất quán về diễn đạt,
trôi chảy và không có lỗi đáng kể trong đoạn ngắn này. Đây là các mốc vận
hành cho sàng lọc, chưa phải thang đo đã được xác nhận độ tin cậy.

Một đoạn có thể rất trôi chảy nhưng sai logic. Đoạn khác có thể không nêu
điều gì sai vì không thực sự kể sự kiện mới: khi đó `new_event=0`. Nếu văn
bản không hiểu được, dùng `unclear=1`; không để việc “không tìm ra lỗi” biến
thành một kết quả đạt. Các trường vẫn cần điền đủ, kèm lý do trong `evidence`.

## Sau khi chấm

Lưu nguyên phiếu đầu tiên; nếu sửa nhãn, giữ bản trước và ghi lý do. Công cụ
chỉ tổng hợp nhãn bạn đã điền, không tự tạo nhãn. Phiếu thiếu vẫn để pending.
Mỗi backbone phải đạt đồng thời các tiêu chí ở ít nhất 12/16 đoạn có điều
kiện, đoạn vô điều kiện cũng phải đạt; nhóm output trùng lớn nhất không quá
4. Đây là rule sàng lọc đã chốt, không phải chứng minh chất lượng hội thoại,
hiệu quả logic chính hay tiêu chuẩn chấp nhận của journal.

Một người chấm không cho phép báo độ đồng thuận giữa hai người. Dữ liệu này
chỉ phục vụ quyết định feasibility của tác giả; đánh giá người đọc cho kết
quả chính vẫn cần được xử lý riêng theo protocol và nguồn lực thật.
