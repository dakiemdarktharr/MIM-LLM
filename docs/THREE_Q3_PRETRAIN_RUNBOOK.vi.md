# Ba bài độc lập: handoff trước train

Ngày 26/11/2026. **Mọi training/fitting vẫn khóa**, kể cả optimizer smoke tests.
Lệnh hoàn thiện B/C không phải lệnh train. Không mở paid Colab runtime trong
phiên chuẩn bị. Gói $50 là thông tin người dùng cung cấp; SKU, CU balance,
GPU và CU/h chưa được xác minh. Mục tiêu dài hạn vẫn là model MIM-LLM hội thoại
hoàn chỉnh; ba thí nghiệm nhỏ chưa chứng minh năng lực chat đó.

## Ba câu hỏi và điều kiện vận hành

| Bài | Câu hỏi | Primary contrast | Dữ liệu trước train |
|---|---|---|---|
| A | Semantic no-op có giúp đổi/giữ hệ quả đúng hơn matched surface edits? | A1−A2 | 6.000/400/400 sources, bốn biến thể |
| B | Semantic-write interference trong giám sát trễ có chuyển sang prose generation? | B2−B1 | 6.000/400/400 event streams, QA branches được tạo theo schedule |
| C | Coupled/off-policy controlled roll-ins có khác nhau khi model tiếp nối sự kiện nó đã viết? | C2−C1, free panel | 600/60/120 source prompts và grammar; production bank chỉ tạo sau shared warm-up thật |

A2 nay là punctuation control khớp byte length và số ký tự sửa, không gọi
paraphrase. B1/B2 có cùng lag 256 và cùng đáp án; B0 immediate được counterbalance
cả vị trí window. C title mới là *Controlled Roll-In Distributions for
State-Consistent Story Continuation*: constrained token sampling ở bank train,
**không mask** ở main evaluation. Origin label không vào model; đây là khác biệt
phân phối input, không một hiệu ứng nguồn gốc nội tại vô hình.

Hai backbone chung: minGRU **2.099.864** tham số và Transformer **2.119.408**,
hai tầng, fixed byte259, context2048, dropout0, float32, microbatch2. Sáu
warm-up ×5M targets được tạo **một lần** theo plan A; B/C kiểm tra đúng plan ID,
seed/kind và checkpoint SHA trước reuse. Không có 18 warm-ups vật lý.

Mỗi bài: 4 arms×2 backbones×3 seeds=24 post runs, **48M supervised targets**,
reserve selection **7,2M**. Toàn bộ ba bài: 30M unique warm-up +144M post +21,6M
reserve=**195,6M** planned targets nếu dùng hết reserve. B tính cả event và QA
labels vào cap; C không tính việc sinh/NLL matching là miễn phí. Equal targets
khác equal compute; cap GPU-hour chung còn phải chốt bằng đo máy/Colab thực.

## Artifact hiện hành

- Data: `data/processed/three-q3-final-reviewed/{a,b,c}`.
- Plans/checks: `artifacts/three-q3-final-20261126/{a,b,c}/plan.json` và receipts.
- Registry/DAG: `artifacts/three-q3-final-20261126/registry.json`, sáu init jobs
  và 72 post jobs, dependencies riêng, post order luân phiên A/B/C.
- Snapshot công khai: `configs/q3{a,b,c}/prepared_snapshot.json`.
- Notebook CPU chuẩn bị: `notebooks/Three_Q3_Prepare_Colab.ipynb`.
- Bundle local: `artifacts/three-q3-pretrain.zip`, không Git.
- Bộ trước đây `q3a-pretrain.zip`/`q3a-final` là lịch sử; dùng registry mới.

## Chuẩn bị/kiểm tra không train

Từ root repo Python3.11+, không chạy command train hoặc chỉnh permission:

```text
python -m pip install -e ".[test,data,notebook]"
python scripts/prepare_three_q3.py --check-devices cpu
python -m pytest -q
python scripts/export_three_q3_bundle.py
```

Script prepare tạo artifact mới hoặc verify artifact đã có; không ghi đè data
và không tự đổi fingerprint. Trước khi tạo lại từ checkout mới, tải đúng
TinyStories revision bằng `mimq3a fetch-warmup --output data/raw/q3a-tinystories.jsonl`
hoặc dùng bundle local đã có corpus/pin/license. Tokenizer byte cố định, không fit.
Không dùng metadata filenames làm feature. Không đưa state table vào inference.

Upload bundle lên `/content/three-q3-pretrain.zip`, mở notebook trên CPU.
Notebook chỉ verify/forward/backward, **Run all không train hoặc collect bank**.
Phiên này chỉ chạy notebook trên máy local; Colab thật chưa kiểm chứng. Nếu
đổi code/data, phải tạo plan mới và kiểm tra lại trước resume; giữ provenance.

## Khi người dùng cấp lệnh train sau này

Không bỏ qua kiểm tra optimizer/memorization/interruption-resume đang bị giữ
lại. Policy cần exact authorized run IDs và plan IDs; không có auto unlock.
Mua subscription hay preflight thành công không tự cấp quyền. Ví dụ cú pháp
dưới đây **chưa phải lệnh được phép chạy**:

```text
mimq3a train --plan A_PLAN --run-id warmup-mingru-s0 --output-root SHARED_RUNS --seconds-limit APPROVED_LIMIT --device cuda
mimq3a train --plan A_PLAN --run-id A1-mingru-s0 --output-root SHARED_RUNS --seconds-limit APPROVED_LIMIT --device cuda
mimq3bc train --plan B_PLAN --run-id B2-mingru-s0 --warmup-root SHARED_RUNS --output-root B_RUNS --seconds-limit APPROVED_LIMIT --device cuda
```

B/C không tự train thêm initialization. A/B post có thể bắt đầu khi parent
tương ứng đủ; C cần bank. Check writing feasibility và GPU/CU trước full grid;
không cố hoàn tất quota khi model chưa viết được hoặc giả thuyết/benchmark lỗi.
Time limit là soft invocation cap; update/save đang chạy có thể vượt ít thời
gian, và nhiều resume không thay global spending cap. [Colab FAQ](https://research.google.com/colaboratory/faq.html)
nêu tài nguyên/runtime không bảo đảm; chọn persistent storage và xác minh SHA.

## C: phụ thuộc bắt buộc sau warm-up, đã có code xử lý

```text
mimq3bc collect-bank --shared-plan A_PLAN --data C_DATA --warmup-root SHARED_RUNS --output C_FEASIBILITY_BANK --source-limit 24 --device cuda
mimq3bc collect-bank --shared-plan A_PLAN --data C_DATA --warmup-root SHARED_RUNS --output C_FULL_BANK --source-limit 600 --device cuda
mimq3bc seal-bank --shared-plan A_PLAN --data C_DATA --warmup-root SHARED_RUNS --bank C_FULL_BANK --output C_MATCHED --device cuda
mimq3bc bind-bank --plan C_BASE_PLAN --bank C_MATCHED --output C_EXECUTION_PLAN
```

Các lệnh là stage tương lai. Không chạy full collection sau feasibility một
cách vô điều kiện: đo cost và kiểm tra yield. Constrained histories có chín
chuỗi hợp lệ, model thật chọn từng token; teacher dùng cùng support. Matching
giữ cùng source/place, giới hạn 32 bytes/0,25 nats-byte, tối thiểu30 sources mỗi
learner và ít nhất một self/peer history khác nhau. Thiếu overlap hoặc hoàn toàn
trùng thì stop không train C; không nới caliper để tìm gain. Source24 feasibility
không đủ ngưỡng30 và không được dùng như bank full. Bound plan mới có hash của
bank và learner SHA; chỉ cấp execution ID trong phạm vi lệnh user đã cho.

Không thể có production self/peer bank thật trước checkpoint warm-up thật.
Teacher fixtures trong preflight chỉ kiểm tra tensor/loss, tuyệt đối không
thay bank C1/C2. Grammar correctness không chứng minh free writing quality.
Đây là phụ thuộc khoa học tự nhiên; việc code-ready không xóa nó.

## Sau post-training

A dùng `mimq3a`; B/C dùng `mimq3bc`: `generate` validation, `probe-evaluate`
(B/component), `freeze-selection`, test `generate`, `blind-packet`, `analyze`,
`results-table`. C eval có free và fixed-history panels; giữ raw first IDs kể
cả byte lỗi/unparsed/no-event, không thay bằng teacher choice. Malformed UTF-8
không được credit strict success. Không dùng parseable-only denominator.

Registration mẫu ở mỗi `configs/q3*/preregistration.template.json`; chốt effect,
resource cap, source sample và selection trước test. Freeze cần đủ24 checkpoint
của bài, giữ toàn source/pair/seed trong sample. Đây là integrity gate nội bộ,
không tự là public preregistration. Data/source/grammar mới và transfer ngoài
template vẫn là science gates trước claim rộng hoặc nộp manuscript.

A packet là CSV như guide trước; B/C packet JSONL có propositions và judgments
để trống, PRIVATE-key không đưa reader. Hai reader độc lập chấm/evidence,
adjudicate disagreements; coverage/fluency được lấy trung bình hai reader khi
không có adjudication. C cần new_event/prefix_valid/followup_consistent, bao gồm
cả format đoạn đầu trong instructions_met. No-event/omission/unclear không được
credit. Báo contradiction types, source-clustered CI và từng seed; CI source
không thay bất định optimizer. Không điền số hoặc nhãn người để hoàn thành draft.

[Rubric B/C và giải thích thuật ngữ](THREE_Q3_ANNOTATION_GUIDE.vi.md) nêu cách
chấm actual event, omission, format, coverage/fluency và adjudication. Rubric còn
phải được pilot bởi người thật trên validation trước khi khóa test.

## Title, methodology, 30 câu hỏi và giới hạn

- [A: brief +10 câu trả lời](Q3_A_BRIEF_AND_ADVISOR_QA.vi.md)
- [B: brief +10 câu trả lời](Q3_B_BRIEF_AND_ADVISOR_QA.vi.md)
- [C: brief +10 câu trả lời](Q3_C_BRIEF_AND_ADVISOR_QA.vi.md)

Bản LaTeX độc lập, tác giả/kết quả trống, không nói một bài phục vụ bài khác.
Drafted-with-results/submitted/accepted/published vẫn chưa đạt. Trường hợp
negative, template-only, thiếu overlap hoặc novelty không đủ phải báo, gộp hay
dừng; không thiết kế loop chạy đến khi đủ ba kết quả thuận chiều.

## Warm-up chung và perplexity

Đính chính vận hành chung 26/11: warm-up thêm 2.792/277/280 ví dụ chỉ dẫn viết
ba câu, tách máy móc từ chính split TinyStories tương ứng. Tổng nguồn gốc vẫn
3.000/300/300; số dòng trộn là 5.792/577/580, không phải số truyện độc lập mới.
Không thêm state labels benchmark, không tăng cap 5M/init. Perplexity chỉ chấm
truyện gốc giữ riêng, loại các dòng chỉ dẫn dẫn xuất. Khả năng viết phải kiểm
tra sau train, không suy ra từ việc đã thêm format examples.

A/B/C có lệnh `perplexity` trên validation. Test perplexity cũng cần selection
lock; không dùng nó để chọn cấu hình. B chấm prose tại cuối high window, không
đưa phần stream chứa lần đổi target kế tiếp vào prompt. C grammar support được
biên dịch từ holder chuẩn ở **train**, là state scaffolding phải công bố; main
inference không nhận grammar hay bảng trạng thái chuẩn.
