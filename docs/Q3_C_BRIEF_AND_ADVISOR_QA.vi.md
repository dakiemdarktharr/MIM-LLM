# Q3-C — nhiệm vụ, phương pháp và 10 câu hỏi khó

**Title cập nhật:** *Controlled Roll-In Distributions for State-Consistent Story
Continuation*. Tên mới phản ánh đúng pilot đã kiểm soát; không nhận một hiệu ứng
nguồn gốc nội tại mà model không được quan sát.

**Nhiệm vụ mục tiêu.** Model tự viết đoạn đầu có sự kiện lưu chìa ở một nơi,
đoạn đó được cố định nguyên văn/raw token IDs. Sau câu hỏi tiếp nối, model viết
3–5 câu theo chính sự kiện ấy. Đo riêng khả năng tạo sự kiện, giữ đúng prefix và
nhất quán ở đoạn sau; không chỉ tính những đoạn parser đọc được.

**Methodology.** C0 controlled teacher histories; C1 frozen peer histories;
C2 frozen learner-initialization histories; C3 teacher/self mixture. Trong pilot
train, self/peer sinh **token-by-token với grammar mask** trên chín đoạn tự nhiên
ba câu: ba vị trí × ba cách diễn đạt. Đó là constrained generation, không phải
free authorship. Peer là seed tiếp theo của cùng backbone, cùng warm-up/data.
Bank được tạo sau shared warm-up thật và đóng băng trước post-training. Matching
giữ cùng source/event location, length caliper 32 byte và frozen-learner surprisal
gap ≤0,25 nats/byte; log toàn bộ offered/rejected/identical histories. Stop khi
thiếu overlap hoặc self/peer trùng hoàn toàn. Primary C2−C1 trên **free-run,
unconditional** pipeline success; common fixed-history panel là secondary.

Tiền lệ gồm [StateWise](https://arxiv.org/abs/2610.33766), self-training đã có,
và [From Simulation to Enaction](https://arxiv.org/abs/2605.25459), nghiên cứu
recognition/surprise của model-origin histories. Novelty không nằm ở tự sinh
data hay grammar mask; cần finding/failure principle có transfer ngoài bank nhỏ.

## 1. Nếu model không thấy nhãn self/peer, “nguồn gốc” có tác dụng độc lập không?

Không có đường nhân quả bí ẩn từ một nhãn metadata không vào model. Arm thay
**phân phối chuỗi input** và độ coupling với learner initialization. Matching
điều kiện hóa estimand lên vùng overlap; không chứng minh pure origin identity.
Đây là lý do đã đổi title và thu hẹp claim.

## 2. Grammar mask có biến lịch sử thành văn teacher viết sẵn không?

Teacher xác định support hữu hạn, còn từng token self/peer được lấy mẫu từ
phân phối LM tái chuẩn hóa trên token hợp lệ. Phải gọi đúng constrained roll-in,
không gọi free writing hoặc thuật toán generation mới. Kiểm soát này giúp biết
chắc state và chất lượng cú pháp; main evaluation bỏ mask hoàn toàn.

## 3. Khác gì self-training, DAgger hoặc StateWise?

Không nhận phát minh self-training hay sửa exposure bias. Bank này cố định từ
initialization, không online aggregation theo policy đang đổi và không preference
optimization. Câu hỏi hẹp là coupled/off-policy roll-in distributions sau semantic/
surprisal matching có khác nhau về generation pipeline hay không.

## 4. Tại sao chưa có bank self/peer ngay trong phiên chuẩn bị?

Chưa được train shared initialization. Lấy teacher templates, model ngẫu nhiên
hoặc checkpoint khác rồi gắn nhãn “self” sẽ sai provenance. Code collector chỉ
nhận checkpoint hoàn tất đúng shared plan. Fixture dùng cho gradient/unit tests
được ghi rõ không phải dữ liệu nghiên cứu C1/C2.

## 5. Khi learner đã cập nhật weights, self bank còn on-policy không?

Không. Self nghĩa là sinh bởi **frozen initialization** của learner, không phải
policy hiện tại sau mỗi update. Vì vậy không được gọi thí nghiệm on-policy.
Muốn refresh online phải thiết kế extension riêng, với ngân sách và estimator
riêng; không âm thầm thay bank giữa một run.

## 6. Gold suffix theo lựa chọn model hay theo ý định teacher?

Theo sự kiện thật trong lịch sử được chấp nhận. Nếu history nói drawer thì
suffix theo drawer; không sửa về basket do teacher từng chọn. Full controlled
grammar được parse chính xác ở train. Free evaluation giữ nguyên raw IDs, kể
cả nội dung không parse được; người đọc đánh giá actual history thay vì loại mẫu.

## 7. Surprisal matching loại hết confound chưa?

Không. Nó khớp một đặc trưng scalar của phân phối input, không khớp mọi đặc
trưng hidden state/style. So cùng source/place, giới hạn độ dài và full grammar
giúp giảm confound; vẫn cần báo residual và chỉ kết luận trên matched subset.
Không có overlap thì stop, không nới caliper đến khi có kết quả thuận chiều.

## 8. Nếu hai bank trùng văn bản thì sao?

Với cùng initialization, targets, thứ tự và optimizer ngẫu nhiên được ghép,
hai input corpora giống nhau cho cùng cập nhật. Origin metadata không thể tạo
lợi ích. Pipeline báo identical-history rate và chặn trường hợp toàn bộ trùng;
không chi compute cho một so sánh không còn khác biệt input.

## 9. Model có thể né sự kiện hoặc giữ nhất quán với một lỗi ban đầu?

Primary unconditional đòi tạo sự kiện theo yêu cầu, không vi phạm prefix, rồi
follow-up nhất quán và đủ mệnh đề/format. No-event, generic và prefix-invalid
đều thất bại; consistency có điều kiện được báo riêng với denominator rõ. Một
đoạn sau lặp lại lỗi của đoạn đầu không sửa được lỗi trước đó.

## 10. Điều gì mới đủ để viết bài, và khi nào phải bỏ?

Hiệu ứng hoặc failure principle phải tồn tại ở free-run/common-history panels,
giữa seed/backbone và nguồn mới, sau kiểm soát coverage/fluency và chi phí bank.
Nếu chỉ học chín mẫu, chỉ giảm entropy, không có overlap, hoặc không có insight
vượt data-quality/style shift, phải thu hẹp, gộp hoặc dừng manuscript. Không
đồng nhất code-ready, parser validity, chat capability hoặc acceptance.


Đính chính vận hành chung 26/11: warm-up thêm 2.792/277/280 ví dụ chỉ dẫn viết
ba câu, tách máy móc từ chính split TinyStories tương ứng. Tổng nguồn gốc vẫn
3.000/300/300; số dòng trộn là 5.792/577/580, không phải số truyện độc lập mới.
Không thêm state labels benchmark, không tăng cap 5M/init. Perplexity chỉ chấm
truyện gốc giữ riêng, loại các dòng chỉ dẫn dẫn xuất. Khả năng viết phải kiểm
tra sau train, không suy ra từ việc đã thêm format examples.

Giới hạn giám sát: grammar train được biên dịch từ holder chuẩn của nguồn.
Đây là state scaffolding ở train, không phải bằng chứng model tự suy ra holder.
Không cấp grammar/holder table khi main inference tự do.
