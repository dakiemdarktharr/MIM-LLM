# Q3-A — 10 câu hỏi bảo vệ đề cương revision 2

25/11/2026. Theo [đề cương hiện hành](Q3_A_STUDY_PLAN.vi.md). Đây là câu trả lời
mẫu cho planning, không phải kết quả đã thu. Lập luận của phiên bản trước còn
trong Git lịch sử và note Advisor-QA của Obsidian.

## 1. Đề tài mới của em là gì, và nó hỗ trợ MIM-LLM thế nào?

“Em nghiên cứu độ đúng của bộ chấm temporal state consistency trong đoạn tiếp
nối 3–5 câu. Bộ chấm phải phân biệt cập nhật hợp lệ, stale state, sai invariant
và thiếu hệ quả bắt buộc. Q3-A cung cấp task contract, rubric và evaluator đã
kiểm chứng cho Q1; B cung cấp bằng chứng train-only supervision; C cung cấp cơ
chế N/S/M và resource matching. Q1 mới là bài chính kiểm tra sai phân tường minh
có lợi hơn learned-pair không. Ba Q3 hỗ trợ Q1 nhưng vẫn cần câu hỏi riêng.”

Mang theo: bản đồ artifact A/B/C→Q1 và kế hoạch source test mới cho Q1. Không nói
Q1 phải đợi cả ba Q3 được nhận, hay cùng một bảng có thể tính thành hai đóng góp.

## 2. CheckEval, OpenMEVA và FactTrack có rồi. Em có gì hơn?

“Em kế thừa Boolean checklist, kiểm chứng metric và biểu diễn hiệu lực thời gian.
Không nhận các cơ chế đó là mới. Phần em cần chứng minh là kết quả thực nghiệm
có kiểm soát khi chấm task temporal story continuation: lỗi nào xuất hiện, có
phân biệt được valid update với stale state không, và phát hiện còn đúng trên
output nguyên trạng chưa dùng chọn protocol không. Nếu grouping không hơn
checklist mạnh, em báo đúng và xem giới hạn/sự đơn giản ấy có insight đủ độc lập
không. Nếu không, em gộp phần hữu ích vào Q1.”

Mang theo: novelty table, adaptation log và tiêu chí dừng. [CheckEval](https://aclanthology.org/2025.emnlp-main.796/),
[OpenMEVA](https://aclanthology.org/2021.acl-long.500/),
[FactTrack](https://aclanthology.org/2025.naacl-long.144/).

## 3. Có phải em cho phương pháp mới nhiều gold information hơn baseline?

“Contrast chính E2−E1 dùng cùng prefix, output, nội dung obligation manifest R,
cùng judge backbone và yêu cầu dẫn chứng. E1 có đầy đủ tiêu chí thời gian,
contradiction và omission; E2 nhóm mệnh đề theo world/time. E0 chỉ đọc prefix/output
là reference pipeline, không dùng E0 để kết luận grouping thắng ở cùng thông tin.
Gold human labels không cung cấp cho evaluator, R không được suy từ output cần
chấm. Generator không thấy state table.”

Mang theo: hai input packet cạnh nhau, prompt-selection budget và token/call
logs. Cùng max tokens không có nghĩa compute thực giống nhau.

## 4. Primary là gì? Tại sao không dùng chính điểm MIM để chứng minh metric tốt?

“Primary là delta balanced accuracy của E2 so E1 trên human semantic-success
labels của output nguyên trạng ở source test giữ riêng. Balanced accuracy trung
bình tỷ lệ nhận đúng lớp thành công và lớp thất bại. MIM thắng không xác nhận
metric; metric phải đối chiếu phán đoán độc lập. Format và fluency báo riêng.
Evaluator abstain/parse-fail vẫn nằm denominator, không được bỏ mẫu khó.”

Mang theo: estimand, class counts, paired source bootstrap 95% CI và xử lý N/A
khi thiếu lớp. SESOI 5 điểm BA là đề xuất trước registration, không phải chuẩn
journal. Không có gain hoặc CI rộng không được gọi tương đương nếu chưa đủ thiết kế.

## 5. Omission không phải contradiction. Em đang cố tạo lỗi cho detector à?

“Đúng, thiếu thông tin không tự là mâu thuẫn. Em không nói detector sai khi nó
không tìm thấy mâu thuẫn trong câu chung chung. Em kiểm tra giới hạn của việc
dùng chỉ số ấy làm đại diện thành công toàn nhiệm vụ. Rubric tách omission,
contradiction, ambiguity và format. E1 mạnh đã có tiêu chí completeness; nếu E2
hơn thì phải vượt đối chứng này, không chỉ thắng một detector mục tiêu hẹp.”

Mang theo: output đúng đủ, đúng nhưng thiếu, cập nhật hợp lệ, stale-state và world
mixing. Không dùng việc metric coverage đổi theo coverage làm chứng cứ validity độc lập.

## 6. Làm sao biết gold đúng, nhất là khi có nhiều cách viết hợp lệ?

“Oracle xác định hệ quả trong microworld đã quy ước; diễn giải prose cần hai người
đọc độc lập và evidence spans. Nhân vật được giả định tuân thủ luật; trigger đúng
9 giờ khác trigger khi điện trở lại. State có world/time/micro-event order;
possession không phải ownership. Không ép mô hình cất chìa đúng một nơi; phần
tiếp nối được chấm theo lựa chọn thật của nó.”

Mang theo: task contract, event ledger, trường hợp 9:05→9:15 và nhãn trước phân
xử. Unresolved ambiguity phải báo và phân tích bounds; không âm thầm loại để tăng điểm.

## 7. Lỗi do em sửa bằng tay có thật sự đại diện lỗi model không?

“Không tự đại diện. Controlled edits chỉ kiểm tra từng failure mode và có người
xác nhận không thêm lỗi ngoài ý muốn. Primary nằm trên output model sinh nguyên
trạng, không chọn riêng những đoạn phương pháp mới thắng. Các biến thể cùng anchor
đều nằm cùng split; thêm nhóm human-authored naturalistic và báo riêng provenance.
Ba bối cảnh cùng trigger schema không được gọi là ba dạng suy luận độc lập.”

Mang theo: sampling/split manifest, edit audit và kết quả controlled đối chiếu
unmodified. Nếu gain chỉ còn trên lỗi sửa tay, thu hẹp claim hoặc dừng.

## 8. Các model 1.7B có đủ làm judge không, và có thiên vị chính nó không?

“Chưa biết. Qwen3-1.7B và SmolLM2-1.7B-Instruct là ứng viên có thể kiểm tra trên
máy, không phải judge đã xác thực. Em đo capability trên dev, VRAM và parser,
chạy E1/E2 cùng backbone rồi replication ở họ khác. Nếu dùng hai họ này cả sinh
lẫn chấm, em phải báo breakdown theo generator để thấy self-preference; chúng
không hoàn toàn độc lập. Em không suy ra kết quả cho frontier models.”

Mang theo: exact model revision, actual parameter counts, input/output tokens và
failure logs. Không tự chuyển sang API trả tiền khi judge nhỏ không đạt feasibility.

## 9. Mẫu có đủ không, và tại sao inference-first vẫn có thể tốn công?

“96 test sources là mục tiêu lập kế hoạch, chưa chứng minh đủ power. Hai premise
và hai generator cho 384 output; hai người đọc 2–4 phút/output cần 25,6–51,2
giờ-người trước controlled set và phân xử. Ba evaluator trên hai judge cần 2.304
calls nếu mỗi lần chấm chỉ một call. Em chọn sample size bằng validation và budget
trước lock; source là đơn vị resample, không phải câu hoặc mỗi call.”

Mang theo: precision/power simulation, annotation timing, CI và call/time budget.
Không dùng training tok/s của MIM để dự báo inference của pretrained judges khác.

## 10. Tại sao journal nên nhận? Nếu kết quả âm hoặc chỉ đủ công cụ thì sao?

“Lý do phù hợp cần là một empirical evaluation có insight, đối chứng mạnh, nhãn
độc lập và phạm vi rõ, không phải lời hứa benchmark đầu tiên. J.UCS là ứng viên
CS có chính sách miễn phí chung; fresh quartile và submission guidelines còn
vướng 403 nên chưa gọi là submission-verified. JLM cần linguistic insight nên
không phải fallback tự động. Không thể bảo đảm acceptance.”

“Nếu nghiên cứu chỉ đủ thành bộ công cụ chấm hoặc không có insight vượt công
trình trước, em gộp nó vào Q1. Null result chỉ đủ bài nếu có precision và giải thích
hữu ích. Khi đưa sang Q1, em khóa rubric/evaluator, dùng source test mới và trích
dẫn kết quả Q3, không công bố lại như mới. Các mốc drafted/submitted/accepted/
published vẫn tách riêng.”

Mang theo: submission evidence checklist, stop/merge rule và bảng đóng góp bốn bài.
