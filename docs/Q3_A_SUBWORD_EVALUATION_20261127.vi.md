# Pipeline đánh giá subword — 27/11/2026

Đây là code chuẩn bị; **chưa có post plan/run, output chính thức hoặc nhãn người**.
Hai parents seed0 đang học foundation; matrix đòi6parents thực, không nhân
seed0 thành3seed. Không thay learning source/fingerprint c18 đang chạy.

Các module mới tách khỏi byte pipeline lịch sử:

- `q3a_subword.evaluate`: chỉ nhận checkpoint post đủ target budget, đúng plan,
  parent/run/tokenizer/config/FP32/backend identity. Test chỉ mở khi24checkpoints
  đã hoàn tất, có writing/validation evidence và local analysis registration.
- `q3a_subword.analysis`: kiểm hash receipt, ID subword nguyên bản và decode
  đúng snapshot, gồm token0 hợp lệ. Từ chối text đã sửa, EOS/BOS/PAD nằm trong
  emitted IDs hoặc metadata lệch nguồn. Không dùng byte-ID259 decoder cũ.
- `q3a_subword.cli`: `freeze-selection`, `generate`, `blind-packet`, `analyze`,
  `perplexity`.
  Xem `python -m mim_llm.q3a_subword.cli --help`; không có lệnh tự train/mở test.

Model chỉ nhận natural prompt. World/mandatory facts lưu trong scoring record
riêng, không truyền bảng trạng thái chuẩn vào model. Mỗi panel giữ nguyên cả
base/effective/noop, cùng decoding128BPE/temperature0,8/top-k40/seed17. Stream
và flush mọi output, kể cả rỗng/chạm cap. Khi lỗi giữ partial file và started
receipt, không có completed receipt và không ghi đè để âm thầm bỏ mẫu xấu.

Backend MHAFalse được giới hạn trong hàm inference, trả flag cũ khi thành công
hoặc lỗi. Runner post chuẩn bị cũng ghi flag này trong identity/environment,
nhưng real post IDs vẫn không được cấp quyền. Hai optimizer/resume tests static
synthetic CPU pass sau sửa, không tạo scientific parents hoặc nhãn người.

## Định nghĩa và đóng test

Với một nguồn và một run, `S_r` bằng1 khi đoạn của role`r` thỏa cả4mandatory
propositions, có3–5câu, không contradiction và không unclear; ngược lại bằng0.
Chỉ số ghép cặp của nguồn:

\[
Y=\tfrac12(S_{base}S_{effective}+S_{base}S_{noop}).
\]

Primary contrast giữ A1−A2 theo từng backbone và seed. Bootstrap resample nguyên
source cluster, giữ các role/cặp/run cùng nguồn; source CI conditional trên các
training seeds đã quan sát, không là bảo đảm biến thiên giữa mọi initialization.
Không dùng số câu làm cỡ mẫu độc lập. Primary analyzer cũ được tái sử dụng,
không đổi định nghĩa để có kết quả thuận chiều.

Freeze đòi24weights, nhưng có thể đăng ký trước chỉ annotate A1/A2 cho cohort
chính; các arm ngoài cohort không được generate test bằng selection đó. Không
trộn cohort/denominator khác nhau. Budget/effect/source sample/analysis hash và
validation evidence phải thật; template còn null, chưa là preregistration đã
hoàn tất hoặc đăng ký ngoài dự án. File test chỉ được byte-hash trước freeze;
kiểm membership source IDs sau khi cấu hình và weights đã chốt, không score.

Packet mù được kiểm full panel, source facts và completed receipts trước khi
sinh CSV trống; model IDs chỉ ở private key. Hai reader **thật, độc lập** và
adjudication cho bất đồng logic vẫn là contract phân tích. Coverage/fluency lấy
trung bình hai reader trừ khi có phân xử explicit; không bịa hoặc tự điền nhãn.
Hiện chỉ tác giả sẵn sàng, chưa có reader thứ hai; pilot34mẫu feasibility với
author-reader là quy trình khác, không thỏa inter-rater confirmation.

Fingerprint post đã thêm imported training-order/primary-analysis sources;
so parent tokenizer theo snapshot/spec, không bắt đường dẫn file giống nhau.
7tests mới kiểm khóa test, thiếu run, parent sai/partial, source/text mutation,
stream interruption, primary-only sample và aggregation từ fictional labels.
Default suite223passed/18trainingdeselected, Ruff pass;2synthetic optimizer
tests pass riêng. Các fixture ghi rõ giả lập, không là human/model results.

Còn trước primary launch: writing feasibility thật,6genuine parents, ngân sách
toàn study và orchestration đo máy thật, general-text PPL thực đo, local analysis
registration/human effort, transfer có quyền dùng và novelty decision. Không gọi
toàn pipeline sẵn sàng hoặc manuscript có kết quả chỉ từ các kiểm tra này.

## Điểm scope cần giải quyết trước post plan

Inspection code generator hiện hành, không phải kết quả model/test: thời điểm
điện về được tạo cách deadline ít nhất4phút; no-op thêm1phút và effective
thường đặt±5phút. Vì thế chưa kiểm đúng ranh giới `power_return == deadline`.
Khi permissionFalse, generator ép điện về sớm; không bao phủ đồng thời thiếu
điện và thiếu permission. No-op chính đổi giờ, chưa kiểm edit permission bị
chặn bởi một điều kiện khác. Không được suy thành khả năng suy luận toàn bộ
ngữ nghĩa hội điều kiện hoặc mọi dạng no-op.

Trước primary training, cần quyết định giới hạn claim hay đăng ký thêm challenge
cohort có boundary/multiple-blocker và sufficient-reason rubric. Nếu thêm, phải
version generator/manifest, giữ paired numeric/BPE controls và freeze cohort
trước xem output; không sửa âm thầm test hiện có. Câu trả lời có nhiều nguyên
nhân hợp lệ không thể bị chấm sai chỉ vì khác một reference reason duy nhất.
Đây là yêu cầu scope đang mở, không bằng chứng tính mới hoặc đã tạo dataset mới.

## General-language perplexity: code có, phép đo mới chưa có

`q3a_subword.language_eval` tính cross-entropy trên toàn vocabulary, không áp
temperature/top-k. Với tổng negative log-likelihood `L` và `N` token đích,
`PPL = exp(L/N)`. EOS vẫn được chấm dù có cùng ID với PAD: chỉ vị trí nhãn
`-100` bị bỏ qua, không bỏ mọi token mang special ID. Token0 là văn bản hợp lệ.
PPL thấp hơn biểu thị dự đoán token tốt hơn trên corpus/tokenizer ấy; không tự
chứng minh đoạn viết hợp logic, tự nhiên hoặc có ích trong hội thoại.

Validation foundation chỉ nhận parent đã hoàn tất cả80M LM và20M SFT; không
mở test foundation. Post test đòi checkpoint/selection đã freeze và đăng ký
`all_frozen_general_test_sources_next_token_with_EOS`, cùng hash nguyên corpus.
Test được tokenize bằng snapshot cố định, mọi source test đều được giữ, reset
trạng thái theo cửa sổ như objective train. Không lấy nhiều cửa sổ cùng truyện
làm nhiều mẫu độc lập: cộng NLL/số token theo source trước bootstrap2000lượt,
seed2026. Khoảng bất định là conditional trên checkpoint, không thay được
biến thiên giữa training seeds. Giữ per-source sums để so sánh ghép cặp sau này.

Hàm inference ghi hash checkpoint, nguồn, tokenizer, số tham số thật, backend,
thời gian và kiểm trọng số không đổi; không có optimizer. MHA/TF32 được trả về
flag ban đầu cả khi lỗi. CLI từ chối output đã tồn tại trước tính toán.
4tests giả lập mới kiểm khóa test trước đọc corpus, EOS/PAD và token0, truyện
dài chia cửa sổ, gom source, bootstrap theo trọng số và parent chưa hoàn tất.
Default suite227passed/18trainingdeselected; Ruff pass. Đây là kiểm code,
**chưa chạy PPL mới trên model thật**. PPL9,4094 đã báo trước thuộc validation
LM80M trước SFT, không được đổi nhãn thành PPL của foundation100M.

**Cập nhật sau lỗi số học lượt6:** [audit backend](Q3_A_FOUNDATION_INVOCATION6_20261127.vi.md)
giữ nguyên FAIL củaFP32/top-k, chuyển mọi generation và PPL mới sangCPU/FP64.
Generator không downcast logits/sampling vềFP32; exact score ties giải theo
tokenID. Receipt/registration/analysis v2 khóa backend này; dữ liệu train và
weights lưu vẫnFP32. Foundation manifest trước đây cần tạo lại cùng prompts
với source hash mới. Các đoạn trước của note mô tả tiến độ lịch sử; kiểm tra
hiện hành232passed/18deselected, chưa có thêm model/human/test results.
