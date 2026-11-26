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
- `q3a_subword.cli`: `freeze-selection`, `generate`, `blind-packet`, `analyze`.
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
toàn study và orchestration đo máy thật, general-text PPL adapter, local analysis
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
