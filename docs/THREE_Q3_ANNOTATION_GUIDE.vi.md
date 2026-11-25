# Hướng dẫn chấm B/C và thuật ngữ chung

Ngày 26/11/2026. **Chưa có nhãn người thật.** Tài liệu này là rubric chuẩn bị;
phải pilot với hai người đọc, sửa ambiguity trên validation rồi cố định trước
test. A dùng [guide hiện có](Q3_A_ANNOTATION_GUIDE.md) với đặc tả operational
trong [joint runbook](THREE_Q3_PRETRAIN_RUNBOOK.vi.md).

## Đơn vị chấm và làm mù

Một item B là prefix và toàn đoạn tiếp nối. Một item C gồm prefix, toàn đoạn
đầu đã cố định, câu hỏi sau và đoạn tiếp nối. Không chỉ chấm các đoạn parser
đọc được. Hai người chấm độc lập nhận `packet.jsonl` và bản `reader-*.jsonl`
tương ứng; không nhận `PRIVATE-key.jsonl`, arm, seed hay checkpoint identity.
Giữ packet/key/test sample cố định. Không nhờ model đóng vai người chấm thật.

Điền `rater_id` thật nhưng có thể dùng mã ẩn danh trong dữ liệu công khai;
`evidence` phải chỉ ra câu/đoạn liên quan hoặc ghi rõ không có evidence. Mọi
proposition/binary field bắt buộc dùng số nguyên0/1; không để null khi submit
nhãn. `unclear=1` nếu ambiguity chưa giải quyết, đồng thời ghi lý do. Những
item ấy ở lại denominator và không được strict success.

## B: ba mệnh đề

- `location`: nói đúng vị trí mới nhất của target tại điểm cắt.
- `latest_update`: xác định đúng cập nhật liên quan cuối, không quay về giá trị
  cũ hoặc coi một delivery của vật khác là cập nhật của target.
- `retention`: giải thích được vì sao các cập nhật khác không làm target đổi
  vị trí; không bịa một lần target di chuyển trước điểm cắt.

Mỗi proposition được1 chỉ khi được diễn đạt đủ rõ và đúng, không chỉ do “không
nhắc đến lỗi”. Một từ vị trí đúng nhưng thiếu đoạn văn/giải thích không qua
primary. Chi tiết mới xảy ra **sau** điểm cắt được phép nếu nhất quán và không
thay thế yêu cầu nói đúng trạng thái tại điểm cắt.

## C: actual history là chuẩn của phần tiếp nối

- `new_event`: đoạn đầu thực hiện việc cất chìa ở một nơi cụ thể theo yêu cầu.
  “Cô sẽ nghĩ một chỗ an toàn” không phải completed storage event.
- `prefix_valid`: đoạn đầu không vi phạm những sự kiện tiền tố và người đang
  giữ chìa; không sửa quá khứ để hợp thức hóa lựa chọn của mình.
- `followup_consistent`: đoạn sau hướng dẫn người bạn theo trạng thái còn hiệu
  lực của **chính đoạn đầu thật**, kể cả nơi ở ngoài chín mẫu grammar train.
- `actual_event_followup`: câu trả lời vị trí/thao tác thực sự theo event đó.
- `valid_explanation`: giải thích phù hợp, không bịa một lần di chuyển chen vào
  để quay về teacher choice hoặc che lỗi.

**Minh họa rubric, không phải output/nhãn người:** nếu đoạn đầu cất chìa vào hộp
giày và đoạn sau chỉ đúng hộp giày, lựa chọn ngoài grammar vẫn có thể hợp lệ.
Nếu đoạn đầu không tạo event thì không được thay bằng drawer của reference.
Follow-up lặp lại một sai phạm của đoạn đầu không sửa được `prefix_valid=0`.

`instructions_met` ở C bao gồm yêu cầu đoạn đầu đúng **ba câu tự nhiên**, sự
kiện được yêu cầu và follow-up đúng nhiệm vụ. `format_3_to_5` chấm đoạn sau
(ở B cũng chấm đoạn tiếp nối). Một item có thể fluent nhưng logic sai hoặc
logic đúng nhưng format sai; giữ các nhãn riêng.

## Trường chung và adjudication

- `contradiction=1` khi có mệnh đề không thể cùng đúng với prefix, lịch sử đã
  sinh hoặc chính các mệnh đề còn hiệu lực. Không nhầm omission với contradiction.
- `contradiction_type`: `none`, `location`, `temporal`, `revision`, `self-event`,
  `cross-world`, `multiple`, `other`. `none` chỉ đi với contradiction0.
- `coverage_fraction`: tỷ phần các mệnh đề bắt buộc thực sự được nói tới,0–1,
  không phải tỷ lệ được nói **đúng**. Sai nhưng có nêu fact vẫn là coverage.
- `fluency_1_to_5`:1=khó hiểu/rời rạc;2=nhiều lỗi;3=hiểu được còn gượng;
  4=tự nhiên với lỗi nhỏ;5=tự nhiên, mạch lạc. Đánh giá riêng correctness.
- `new_event/prefix_valid/followup_consistent` không dùng ở B, giữ null.

Hai reader không xem nhãn nhau trước khi nộp. Bất đồng logic/type/format/unclear
phải được adjudicate bằng evidence; bản adjudicated chứa **toàn bộ** item với
schema như bản reader, không chỉ các hàng bất đồng. Giữ hai nhãn gốc. Báo
pre-adjudication agreement/kappa; kappa có thể undefined khi marginals suy biến.
Quality scores được lấy trung bình hai reader khi không có adjudication.
Không để người biết arm tùy chọn mẫu “đại diện đẹp”; dùng source sample đã khóa.

## Chấm thành công và giới hạn

B strict success cần mọi proposition đúng, instructions/format đúng, không
contradiction/unclear. C thêm new_event, prefix_valid và followup_consistent.
Code cũng không credit invalidUTF8 ở strict metric. Báo coverage, omissions,
contradiction type, fluency và conditional consistency với denominator riêng.
Source clusters, không phải từng câu, là đơn vị bootstrap; show từng seed.
Reader pilot có thể cho thấy rubric chưa đủ tin cậy: sửa trên validation và
đăng ký lại trước test, không sửa nhãn để ra hiệu ứng thuận chiều.

## Thuật ngữ cho người mới

**Autoregressive LM** dự đoán từng token:
`p(x_1,...,x_T)=product_t p(x_t | x_<t)`. Ở đây token thường là byte UTF-8;
một ký tự tiếng Việt có thể chiếm nhiều byte. BOS/EOS/PAD là token đặc biệt.

**Cross-entropy (CE)** là trung bình `-log p(token đúng | tiền tố)` trên các
vị trí có nhãn. Prompt/padding được mask không góp CE, nhưng prompt vẫn tốn
compute. Nhãn dịch một token: logits sau x_t dự đoán x_(t+1). **Perplexity**
là `exp(CE)` trên corpus giữ riêng; tokenizer này cho byte-level PPL, không
so trực tiếp với word/BPE PPL và không thay phép đo logic.

**Semantic no-op** thay tiền đề nhưng giữ một hệ quả đang xét; không buộc mọi
fact hay wording giống nhau. **Semantic write** là cập nhật làm giá trị trạng
thái đổi thật. **Probe** là câu hỏi thành phần, không phải primary prose metric.

**JS divergence** đối xứng là `(KL(p||m)+KL(q||m))/2`, `m=(p+q)/2`; KL đo
độ khác hai phân phối. A3 chỉ áp vào invariant factual-answer spans lúc train,
không ép hai truyện có cùng mọi token. Extra passes phải tính compute.

**Roll-in** là lịch sử dùng làm input khi học viết tiếp. **Frozen bank** giữ
nguyên sau collection; khi learner đổi weights nó không còn on-policy.
**Surprisal** là negative log probability; C khớp mean nats/byte kể EOS dưới
frozen learner. **Caliper** là ngưỡng chênh cho phép khi ghép mẫu, không phải
bằng chứng đã loại mọi confound. **Backbone** là model cơ sở chung trước khi
đổi recipe; **seed** điều khiển randomness, không phải một test source mới.
