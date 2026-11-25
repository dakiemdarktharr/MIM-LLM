# Q3-A — nhiệm vụ, phương pháp và 10 câu hỏi khó

**Title:** *Learning When a Premise Change Should Not Change a Story*.
Trạng thái: chuẩn bị trước train; chưa có kết quả, nhãn người hay quyết định biên tập.

**Nhiệm vụ mục tiêu.** Từ truyện có chuyển giao chìa, điều kiện điện/permission
và mốc quyết định, viết tiếp 3–5 câu. Model phải đổi hệ quả khi tiền đề mới buộc
đổi, đồng thời giữ những dữ kiện còn đúng. No-op chỉ giữ hệ quả đang chấm, không
có nghĩa toàn bộ thế giới giữ nguyên: giờ điện về vẫn thay đổi.

**Methodology.** A0: effective-only; A1: effective + semantic no-op; A2:
effective + surface-form control; A3: A1 + JS trên factual-probe spans invariant
lúc train. A2 vận hành sửa dấu kết câu, giữ nghĩa và khớp byte length/số ký tự
sửa với numeric no-op; **không gọi đó là semantic paraphrase**. Primary A1−A2.
Các arm có cùng source order/reference targets, 2M CE targets/run, cùng hai
backbone và ba seed. Gold state không vào generator ở inference. Chấm joint
success của base/effective và base/no-op, trung bình cân bằng theo source;
bootstrap source-paired, báo từng seed, coverage/contradiction/fluency/PPL riêng.

**Đóng góp có điều kiện:** selective transfer hoặc failure principle vượt mẫu
clock/punctuation và lượng data. Không nhận invariance loss là mới; các tiền lệ
gần gồm [DTO](https://arxiv.org/abs/2605.24885) và
[Counterfactual Invariance](https://arxiv.org/abs/2610.22942).

## 1. Điều gì mới hơn invariance training đã có?

Câu hỏi là tác dụng của **nội dung semantic no-op trong curriculum**, với trần
targets, source order và surface edits được kiểm soát, trên hệ quả đổi/giữ khi
model viết tự do. JS là adaptation đối chứng thứ cấp. Nếu chỉ tăng no-op accuracy
trên mẫu đã học, chưa có đóng góp đủ độc lập để nộp.

## 2. Vì sao đổi 8:50 thành 8:55 vẫn là can thiệp thật?

Giá trị thời điểm trong thế giới thực sự đổi. Với ngưỡng 9:00 và permission
không đổi, hành động đúng vẫn là mở. Không ép model kể cùng giờ hoặc cùng wording;
chỉ buộc giữ những hệ quả còn đúng. Đổi 8:55 sang 9:05 là effective ở trường hợp
permission cho phép, vì trạng thái tủ tại 9:00 buộc khác.

## 3. Punctuation control có quá yếu không?

Nó kiểm soát chính xác byte length và số ký tự sửa, nhưng không bao phủ mọi
semantic paraphrase; vị trí sửa và loại ký tự vẫn khác. Vì vậy primary claim
hẹp hơn “tác dụng thuần semantic”. A3 và chuyển giao sang cách diễn đạt/nguồn
mới là đối chiếu bổ sung; nếu hiệu ứng biến mất ngoài template thì phải thu hẹp
hoặc dừng claim, không gọi punctuation là đối chứng toàn diện.

## 4. Model có thể chỉ dùng giờ hoặc tên cuối cùng?

Permission cũng có thể làm hành động đổi; có nhiều lần handover và cancelled
plans. Việc nhắc tên cuối không tự xác định người giữ chìa. Vẫn cần báo kết quả
các shortcut rõ ràng và phân tầng theo loại can thiệp/depth; bộ kiểm soát này
chưa chứng minh đã loại mọi shortcut ngôn ngữ.

## 5. Giảm mâu thuẫn bằng cách viết chung chung thì sao?

Primary đòi đủ các mệnh đề bắt buộc và format 3–5 câu. Không nói ai giữ chìa
hoặc chuyện gì xảy ra không được tính là nhớ đúng. Báo coverage/omission cùng
contradiction và fluency; một câu không nhắc fact không mặc nhiên là fact sai.

## 6. JS có vô tình ép hai truyện giống toàn bộ không?

Không. Nó so phân phối next-token chỉ tại answer spans của probe thật sự
invariant, với teacher-forced answer prefix căn chỉnh. Công thức dùng JS đối
xứng; probe types cycle qua holder/action/cabinet/power/permission. Không match
toàn continuation, vì model được phép chọn chi tiết mới hoặc kể thời điểm khác.

## 7. Có rò gold state vào câu trả lời lúc test không?

Generator chỉ nhận prompt văn bản. State/probe metadata dùng cho supervision
đã khai báo và scoring; packet người đọc giữ key hệ thống riêng. Test hash không
đủ để mở test: còn cần freeze checkpoint, decoding, sample và analysis rule.
Tokenizer byte cố định không fit lên validation/test.

## 8. “Cùng ngân sách” chính xác là gì?

Hai model có 2.099.864 và 2.119.408 tham số, chênh khoảng 0,93%, không bằng tuyệt
đối. Mỗi arm có cùng CE target cap. A3 có thêm probe passes nên phải log input
tokens/time; parameter-matched, target-matched và compute-matched là các điều
kiện khác nhau. GPU/CU thực chưa đo, không suy tốc độ từ forward-only checks.

## 9. Khoảng tin cậy có coi từng câu là một mẫu không?

Không. Hai premise variants, nhiều output và các seed cùng source được giữ
trong cụm. Resample source paired giữa arm; báo từng seed. CI theo source có
điều kiện trên seed đã chạy, không thay cho bất định do khởi tạo. Không chọn
seed/metric thuận chiều rồi báo như một confirmatory result.

## 10. Kết quả nào khiến phải dừng hoặc đổi bài?

Chỉ tăng trên clock/punctuation templates; lexical shortcut giải thích hết;
writing/coverage giảm; effect quá bất định; hoặc không có insight vượt những
invariance studies gần. Có thể báo negative result có phạm vi rõ, gộp hoặc bỏ
bản thảo. Chưa có cơ sở đảm bảo novelty, quartile hay acceptance từ code/preflight.


Đính chính vận hành chung 26/11: warm-up thêm 2.792/277/280 ví dụ chỉ dẫn viết
ba câu, tách máy móc từ chính split TinyStories tương ứng. Tổng nguồn gốc vẫn
3.000/300/300; số dòng trộn là 5.792/577/580, không phải số truyện độc lập mới.
Không thêm state labels benchmark, không tăng cap 5M/init. Perplexity chỉ chấm
truyện gốc giữ riêng, loại các dòng chỉ dẫn dẫn xuất. Khả năng viết phải kiểm
tra sau train, không suy ra từ việc đã thêm format examples.
