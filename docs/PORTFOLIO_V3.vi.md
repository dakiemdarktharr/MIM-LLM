> **Cập nhật 26/11/2026:** đặc tả vận hành mới ở [joint handoff](THREE_Q3_PRETRAIN_RUNBOOK.vi.md) và [QA hiện hành](THREE_Q3_PRETRAIN_QA.vi.md). A2 dùng punctuation control khớp byte/edit; C dùng controlled roll-in distributions. Các cấu hình, artifact IDs và kết quả kiểm tra cũ dưới đây là lịch sử; không dùng để resume plan mới.

# Bốn hướng nghiên cứu độc lập — revision 3

Ngày 25/11/2026. **Research planning; chưa có kết quả khoa học mới.** Bản này thay
thế định hướng hiện hành của cả bốn bài. Các revision trước là lịch sử. Q3/Q1
chỉ là nhãn mục tiêu nội bộ, không phải hạng của một bài đã được nhận.

**Làm rõ mục tiêu ngày 26/11:** đích dài hạn là mô hình MIM-LLM hội thoại nhiều
lượt hoàn chỉnh, không dừng ở benchmark truyện hoặc bốn bài báo. Các thiết kế
dưới đây là nghiên cứu thành phần; xem [mục tiêu khả năng và lộ trình chat](PROJECT_OBJECTIVE.vi.md).
Việc làm rõ này không tăng ngân sách hay thay câu hỏi/đối chứng đã định.

**Cập nhật vận hành Q3-A ngày 26/11:** đã chuẩn bị pipeline với tokenizer byte
259, context 2.048, minGRU 2.099.864 và Transformer 2.119.408 tham số. Các ví dụ
đếm BPE-512/context-256 bên dưới là lịch sử cho A. Xem [handoff trước train](Q3_A_PRETRAIN_RUNBOOK.vi.md).
Chưa train; không fit tokenizer. Credit warm-up giữa ba bài chỉ có hiệu lực khi
thật sự dùng cùng checkpoint/corpus/config; khi chạy A riêng phải báo đủ physical
warm-up, không nhận sharing chưa xảy ra. Trần post-training/selection vẫn ngang nhau.

Yêu cầu áp dụng: ba nghiên cứu Q3 đều có huấn luyện và cùng trần ngân sách;
mỗi bản thảo tự trình bày vấn đề, tài liệu, phương pháp và bằng chứng của mình.
Không đặt tên chương trình, nhãn quartile, mục tiêu hỗ trợ bài khác hoặc kế hoạch
xuất bản trong nội dung khoa học của bản thảo. Tác giả chưa được xác nhận thì
để trống; không đặt một chương trình nghiên cứu vào vị trí tác giả.

## 1. Bốn câu hỏi sau rà tài liệu

| Track | Tiêu đề làm việc | Câu hỏi chính | Đóng góp chỉ được nhận sau bằng chứng |
|---|---|---|---|
| Q3-A | **Learning When a Premise Change Should Not Change a Story** | Cặp can thiệp không đổi hệ quả có giúp huấn luyện mô hình vừa đổi đúng hệ quả cần đổi, vừa tránh đổi sai dữ kiện còn đúng, vượt paraphrase augmentation cùng ngân sách không? | Phát hiện về độ chọn lọc của counterfactual training và khả năng chuyển sang truyện mới; không nhận invariant training là mới. |
| Q3-B | **Tokens or State Changes? A Controlled Study of Delayed Supervision for Compact Language Models** | Khi giữ lượng nhãn/định dạng câu trả lời, huấn luyện với độ trễ token và nhiễu do cập nhật trạng thái khác nhau ảnh hưởng việc viết tiếp ra sao? | Phân biệt tác dụng của semantic interference với token delay/QA format, xử lý một điểm chưa tách được trong tài liệu gần. |
| Q3-C | **Whose History Should a Language Model Learn From? State-Consistent Continuation from Model-Written Events** | Với chất lượng/loại sự kiện được kiểm soát, lịch sử do chính checkpoint ban đầu viết có lợi hơn lịch sử từ model khác hoặc teacher khi train tiếp nối không? | Bằng chứng về provenance của roll-in và độ nhất quán với lựa chọn thật đã sinh; không nhận self-training hay exposure-bias correction là mới. |
| Q1 candidate | **Branch-Residual Nested Memory for Multi-World Language Modeling** | Một trạng thái prefix dùng chung và các residual state theo thế giới có giữ được chất lượng/ít lẫn nhánh hơn ở cùng ngân sách bộ nhớ so với nhân bản state đầy đủ và recurrent controls mạnh không? | Cơ chế kiến trúc mới có điều kiện, trade-off memory–quality, phân tích lỗi/giới hạn và transfer. Chưa xác lập tính mới hoặc impact. |

Không thể bảo đảm bốn bài có novelty cao bằng đổi tên. Ba Q3 hiện là **câu hỏi
thực nghiệm có điều kiện**, cần insight vượt đối chứng mạnh; Q1 là **ứng viên
kiến trúc rủi ro cao**, không phải một đóng góp đã được chứng minh. Nếu công trình
gần trùng hoặc pilot chỉ cho kết quả hiển nhiên, đổi/gộp/dừng hướng đó trước khi
chi hết ngân sách. Không giữ một manuscript yếu để đạt số lượng.

## 2. Những đối thủ khiến kế hoạch cũ không đủ

Nguồn/phạm vi/mức đọc chi tiết ở [novelty audit](NOVELTY_AUDIT_V3.vi.md).

- [DTO, 2026](https://arxiv.org/abs/2605.24885) đã có objective khả vi để đổi đúng
  phần truyện và giữ phần phù hợp. [Counterfactual Invariance, 2026](https://arxiv.org/abs/2610.22942)
  đã regularize invariance của open-ended responses. A không thể chỉ thêm một
  consistency loss rồi coi là mới.
- [Delayed Supervision, 2026](https://arxiv.org/abs/2609.32312) đã đặt QA sau nhiều
  token/write; chính phần limitations chưa tách rõ delay với QA/termination và
  thêm compute. B nhắm câu hỏi kiểm soát này, không nhận phát minh delayed labels.
- [StateWise, 2026](https://arxiv.org/abs/2610.33766) đã self-train trên trajectory
  có state checker và preference learning; [DAgger](https://proceedings.mlr.press/v15/ross11a.html),
  [Scheduled Sampling](https://proceedings.neurips.cc/paper/2015/hash/e995f98d56967d946471af29d7bf99f1-Abstract.html)
  đã xử lý phân phối lịch sử do model tạo. C phải cô lập provenance, không chỉ
  đổi tên một recipe self-training.
- [Gated DeltaNet](https://arxiv.org/abs/2412.06464), [RWKV-7](https://arxiv.org/abs/2503.14456),
  [KDN](https://arxiv.org/abs/2609.07816), [EDA](https://arxiv.org/abs/2606.26560)
  và [Nested Learning](https://proceedings.neurips.cc/paper_files/paper/2025/hash/4309616aaed8e848009bc4a7ef73b493-Abstract-Conference.html)
  khiến “thêm gate”, “dùng delta” hoặc “bộ nhớ lồng nhau” không đủ novelty kiến trúc.
- [Low-Rank Latent Carriers](https://arxiv.org/abs/2608.15156) đã khảo sát can thiệp
  low-rank trong recurrent world model; [δ-mem](https://declare-lab.github.io/projects/online-memory/)
  có low-rank associative memory và nhiều state. Nén nhánh bằng residual phải
  vượt các tiền lệ này và đối chứng fork/copy đơn giản, không nhận low-rank là mới.
- [DASC](https://arxiv.org/abs/2608.30386) đã nén recurrent checkpoints cho prefix
  reuse; [MoDr, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/8a81180649011d1690e05c68bfeaa57c-Abstract-Conference.html)
  đã có low-rank adapter branches và hard routing cho depth recurrence. Phải
  phân biệt slow-weight adapters với **persistent state residuals**, và cached
  checkpoint reuse với **compressed per-token state evolution**. Khác biệt này
  là câu hỏi cần kiểm chứng, chưa tự đủ một novelty claim.
- Lượt Undermind mới hoàn tất ngày 25/11 còn nêu [SEED](https://arxiv.org/abs/2611.06084)
  (state sink + low-rank working memory), [TreeWY](https://arxiv.org/abs/2608.20961)
  và [Flide](https://arxiv.org/abs/2610.42148) (fork/branch execution), cùng
  [NarraWorld](https://arxiv.org/abs/2609.32401) (world/belief/hypothetical graph
  memory). Đây là novelty threats bắt buộc, không được chỉ so với full-copy yếu.
  **Novelty gate của Q1 hiện vẫn mở**, đặc biệt phải vượt một compressed-state
  baseline có prefix sharing/forking hợp lệ. Không nhận sink-plus-low-rank hoặc
  possible-world memory là phát minh của đề tài.

## 3. Ngân sách huấn luyện chia đều

Chọn **hai backbone hiện có** làm nền chung: minGRU và causal Transformer. Chúng
đại diện recurrence và attention; không khẳng định hai model bao phủ mọi LM.
Mỗi Q3 có **4 arms × 2 backbones × 3 training seeds = 24 run**. Ba seed là mức
khởi đầu; vẫn báo từng seed, không giả vờ đủ precision nếu CI rộng.

Số tham số **đã instantiate và đếm**, chưa train cấu hình này trong revision:

| Backbone | Vocab / layers / context | Width | Tham số backbone thực |
|---|---|---:|---:|
| minGRU | 512 / 2 / 256 | 604 | **2.081.384** |
| Causal Transformer | 512 / 2 / 256 | 268 | **2.074.320** |

Chênh lệch giữa hai cấu hình khoảng 0,34%; không gọi là bằng tuyệt đối. Context
256 chỉ là cấu hình để đếm/khởi tạo, **chưa đủ bảo đảm chứa toàn truyện và output**.
Chốt context chung bằng tokenizer thật trước chạy; thay config phải đếm lại.
Prototype vector MIM-LM BPE-512 cũ có **2.081.472** tham số, không phải số tham số
của kiến trúc residual mới chưa triển khai. Không dùng kích thước danh nghĩa
model thay số thực. Nếu thêm head/adapter, ghi thêm tổng và actively updated P.

### Tiers lập kế hoạch, không phải lượng dữ liệu đã đủ khoa học

| Khoản | Pilot mỗi Q3 | Confirmatory mỗi Q3, chỉ khi có gate |
|---|---:|---:|
| Post-training / run T | 2M target tokens | 10M target tokens |
| 24 runs | **48M** | **240M** |
| Selection reserve tối đa 15% post targets | **7,2M** | **36M** |
| Credit 1/3 warm-up dùng chung | **10M** | **40M** |
| Tổng credit / bài | **65,2M** | **316M** |

Warm-up thực chạy một lần cho 2 backbones×3 seed: W=5M/run ở pilot ⇒ **30M**
targets duy nhất; W=20M/run ở confirmatory ⇒ **120M** duy nhất. Mỗi arm post-train
fork từ cùng checkpoint tương ứng. Do đó ba Q3 cộng lại là **195,6M** targets
pilot với toàn reserve, hoặc **948M** confirmatory với toàn reserve; không nhân
ba warm-up vật lý rồi tuyên bố đã chạy thêm. Nếu đi từ pilot lên confirmatory,
ghi rõ run nào được tiếp tục hay thay mới; không cộng hai tier như hai phát hiện.

Các số trên là **trần thiết kế**, không bảo đảm model biết viết. Warm-up quá nhỏ
thì cả ba cùng dừng ở feasibility; không cứu một bài bằng cách tăng train ngầm.
Không train cho đủ quota khi hướng đã bị bác bỏ.

### Công bằng tài nguyên ngoài target tokens

Token target bằng nhau chưa khớp compute: paired passes, QA prefix replay và
roll-in generation tốn thêm. Mỗi Q3 có cùng **GPU-hour cap G**, chốt sau profile,
cùng policy selection và riêng log training / generation / annotation. Nếu cap
G không đủ hoàn tất cùng token budget, sửa budget chung **trước test**, không
so vài run bị cắt với vài run đủ. Phép so token-matched và compute-matched là
hai điều kiện riêng; báo cả sai lệch còn lại.

Giữ cùng tokenizer/corpus pretrain, split nguồn, target budget, optimizer policy
và decoding trong mỗi phép so. Corpus post-train chỉ khác yếu tố nghiên cứu được
khai báo; kiểm soát chất lượng, độ dài và nhãn liên quan. Đếm processed input
tokens ngoài CE targets, aux targets, FLOP proxy, actual VRAM/time và search budget.
Không coi rollout time là train time, và không đếm nhãn human như dữ liệu đã có.

Máy đã xác minh trước: RTX 5050 Laptop, 8.151 MiB. **Throughput của hai cấu hình
mới, GPU-hours, Colab CU/h và tổng chi phí: chưa đo.** Không dùng 509,72 tok/s
của MIM smoke corpus để tính thời gian cho minGRU/Transformer này. Không mua API
hay cloud mặc định. Lịch GPU dự kiến round-robin A/B/C cùng hạn mức; Q1 có ngân
sách riêng sau novelty/feasibility gate, không lấy reserve của một Q3 mà không
ghi lại quyết định.

## 4. Q3-A: can thiệp có chọn lọc trong dữ liệu huấn luyện

**Estimand chính:** A1−A2 về tỷ lệ cặp tiếp nối thỏa tất cả hệ quả buộc đổi/giữ,
không mâu thuẫn, ở source test chưa thấy. So với A0 và A3 là secondary có kế hoạch.

| Arm | Được train trên gì? | Câu hỏi phân biệt |
|---|---|---|
| A0 | Cặp effective intervention, CE; resample để đủ cùng targets. | Mốc chỉ học các trường hợp cần đổi hệ quả. |
| A1 | Effective + semantic no-op, cân bằng trước train. | Có học được khi nào đổi một tiền đề không đổi hành động bắt buộc? |
| A2 | Effective + paraphrase controls, token/edit-distance/độ khó tương đương khi khả thi. | Gain có chỉ là lexical augmentation/đa dạng hơn? |
| A3 | Cùng mixture A1 + response-matching adaptation trên các factual-probe spans được xác định invariant. | Đối chiếu một invariance-training approach mạnh, không chỉ CE. |

No-op nghĩa là một tiền đề thật sự đổi nhưng hệ quả được hỏi không đổi, ví dụ
8:50→8:55 trước ngưỡng 9:00. Không gọi toàn thế giới là invariant: giờ điện về
vẫn đổi và có thể được kể đúng trong văn bản. Không ép hai continuation có cùng
wording, cốt truyện tự do hoặc nơi cất chìa. A3 chỉ match phân phối của cùng probe
answer bắt buộc còn đúng, không match toàn đoạn văn chứa dữ kiện được phép đổi.
Đó là adaptation có giới hạn của CFI, không full reproduction hay objective mới.
Chi phí/aux targets A3 phải tính; primary A1−A2 không dựa vào A3 hơn vì thêm nhãn.

Train/validation/test giữ riêng source và paraphrase family. Có cả nhánh crossing
và no-op trong test, vary ngưỡng/giờ/đối tượng và reject shortcuts clock-only/
last-mentioned trên development. Nhóm do người viết/có phép bắt buộc ở evaluation;
không gọi template naturalistic là truyện thu thập tự nhiên.

**Bằng chứng tối thiểu:** hiệu ứng có chọn lọc ở changed lẫn preserved, vượt
paraphrase control, không do nói ít hơn/fluency giảm, tồn tại ngoài một template.
**Nguy cơ novelty:** cao vì DTO/CFI/TIME TRAVEL; nếu chỉ chứng minh thêm no-op vào
train thì no-op accuracy tăng, chưa đủ. Cần transfer hoặc failure principle có
ích sau kiểm soát lexical shift. Giảm claim/gộp/dừng nếu không có.

## 5. Q3-B: semantic interference và thời điểm giám sát

**Estimand chính:** B2−B1 trên semantic continuation success ở held-out write
density/delay; không dùng probe accuracy một mình làm thành công.

| Arm | Probe training | Vai trò |
|---|---|---|
| B0 | Immediate QA sau bằng chứng/cập nhật liên quan. | Control cùng question/answer format và số nhãn. |
| B1 | Token-delayed QA, ít intervening state writes. | Độ trễ/độ dài với semantic interference thấp. |
| B2 | QA cùng dải token delay, nhiều writes lên thực thể khác. | Tác dụng của semantic interference trong lịch train. |
| B3 | Mixture B1/B2 được khóa tỷ lệ. | Control đa dạng lịch, kiểm tra trade-off thay vì chọn một delay thắng. |

Event LM corpus giống nhau; chỉ placement/selection của các probe thay đổi.
Cân bằng fact/query types và answer classes; không đổi nhãn đúng vì query muộn.
Retention facts phải vẫn đúng suốt khoảng trễ; revision facts được tính từ lần
cập nhật liên quan cuối. Question/answer nằm trên disposable branches, không thêm
đáp án vào event stream đang tiếp tục. Cùng số answer targets và EOS; prefix
replay và gradient span khác nhau phải log, rồi thêm compute-matched replication
theo budget đã định. Không nhận B2−B1 là tác dụng thuần của thời gian nếu semantic
content/budget chưa kiểm soát được.

**Novelty còn lại:** kiểm định có đối chứng một confound tài liệu gần đã công
khai, cộng chuyển từ delayed QA sang generation. Tăng seed hoặc đổi backbone
không tự là novelty. Nếu mô hình chỉ trả lời probe tốt mà không viết tốt, báo
đúng khoảng cách; không dùng kết quả đó làm bằng chứng LM có bộ nhớ hữu ích hơn.

## 6. Q3-C: nguồn gốc lịch sử mô hình được học tiếp

**Estimand chính:** C2−C1 về consistency với sự kiện mới thật sự được viết ở
đoạn đầu, trên các source test độc lập. C2−C0 và mixture là secondary.

| Arm | Roll-in histories | Khác biệt được kiểm tra |
|---|---|---|
| C0 | Teacher-authored/controlled histories. | Reference sạch, có nhiều cách viết hợp lệ. |
| C1 | Histories từ frozen peer backbone/checkpoint. | Model-generated data nhưng khác nguồn model. |
| C2 | Histories từ chính frozen initialization checkpoint của learner. | Self-origin thay vì mọi model-generated history đều như nhau. |
| C3 | Mixture teacher/self, tỷ lệ khóa trước. | Trade-off đa dạng/ổn định; không giả định self-only tốt nhất. |

“Self” ở đây là nguồn checkpoint ban đầu, **không gọi on-policy** sau khi learner
đã đổi weights. Chốt frozen bank trước run; nếu thử online refresh thì là extension
riêng với call budget bằng nhau và không viết như cùng thí nghiệm.

Trong train controlled subset, parser/oracle chỉ gán sự kiện không mơ hồ đã audit;
suffix target phải phù hợp lựa chọn thật, không thay bằng ý định teacher cũ.
Matching source/event type, semantic difficulty, length, validity và coverage
giữa self/peer; ghi cả rejection/parse yield. Không giữ chỉ phần self đẹp rồi
so với toàn bộ peer. Nếu matching thất bại, không kết luận causal effect của
provenance. [From Simulation to Enaction](https://arxiv.org/abs/2605.25459) đã
chỉ ra model có thể nhận ra on-policy generations và input surprise ảnh hưởng
output entropy. Vì vậy train-bank matching còn phải xét frozen-learner surprisal;
báo overlap/yield và các strata, không nhận giảm entropy đơn thuần là memory gain.
[Causal History Effects](https://arxiv.org/abs/2609.05882) cũng đã can thiệp lên
assistant histories. Nếu không tách được content/quality/surprisal, C phải giảm
claim. Evaluation dùng prose tự do, frozen raw token IDs và human review;
không chỉ chấm những đoạn parser hiểu. Generation failures và omission vẫn trong
denominator. Nhất quán với một lỗi đầu tiên không xóa lỗi với prefix.

**Novelty gate:** phải có insight về provenance ngoài self-training/StateWise,
vượt giải thích data quality hoặc format. Nếu chỉ thêm generated text vào train
và thấy tăng điểm, chưa đủ. Nếu warm-up không sinh được sự kiện rõ, dừng feasibility;
không giả teacher histories là self-generated data.

## 7. Q1: ứng viên kiến trúc, không chỉ ghép ba recipe

MIM gốc dùng hiệu hidden state liên tiếp qua N→S; chuyển convolution sang vector
được giữ làm **baseline kế thừa**, không tự là kiến trúc mới. Hướng rủi ro cao là
**shared-prefix residual recurrent memory**: lưu một snapshot prefix chung và
residual riêng cho từng tình huống sau điểm phân nhánh.

Schematic, **chưa triển khai**, không phải phương trình MIM gốc:

\[
m_{t,w}=s_{\mathrm{fork}}+U r_{t,w},\quad
\delta_t=P h_t-P h_{t-1},\quad
r_{t,w}=E\!\left(F_{N\to S}(s_{\mathrm{fork}}+U r_{t-1,w},x_t)-s_{\mathrm{fork}}\right).
\]

U/E là slow parameters chung; r là recurrent residual có kích thước nhỏ hơn full
state; router chọn world từ visible context/own generated history, không từ
gold state table. Phải đặc tả toàn bộ H/N/S/C/M, previous-lower-state và scratch
state; công thức trên là abstraction, không phải đặc tả train-ready. Routing
oracle chỉ là diagnostic được gắn nhãn riêng; main inference dùng predicted
routing. Mọi auxiliary world labels ở train phải có đối chứng được tiếp cận
thông tin/chi phí tương đương.

Giả sử S là tổng state values của một full trajectory, R là residual values mỗi
world, K là số nhánh cùng fork. Storage dự kiến S+KR+metadata, so với KS ở full
copy. Phải tính routing/scratch state, precision và peak VRAM thực; không chỉ
tính C rồi bỏ H/N/S/M. Không gọi constant-memory theo K, không coi parameter
count là state bytes. Nested forks có thêm snapshots: savings có thể mất khi
số fork tăng hoặc residual cần full rank. Đây là điều phải đo.

Low-rank intervention-entry có tiền lệ và không chứng minh state dynamics nằm
mãi trong một subspace cố định. Bắt buộc kiểm tra rank/horizon và learned versus
random bottleneck; tránh kết luận “state semantics chỉ có vài chiều”. Không nhận
copy-on-write/fork cache, gating hay low-rank riêng lẻ là mới.

### Đối chứng quyết định

- Flat vector MIM-LM, learned-pair thay explicit difference, no-N/no-S/no-M.
- Full per-world recurrent-state copies; unstructured recurrent memory cùng state
  bytes; residual bank không N/S; learned so fixed/random low-rank projection.
- Low-rank recurrent state không shared-prefix anchor; compressed-checkpoint/
  bounded replay reference theo DASC khi áp dụng; MoDr-style parameter branches
  chỉ được gọi adaptation nếu không tái lập hệ đầy đủ. Không so sparse state
  compression với một baseline full-copy bị bỏ mất prefix reuse được phép.
- SEED-style sink/low-rank state và TreeWY/Flide-style fork reference khi đúng
  architecture. Nếu chỉ adaptation, ghi phạm vi; không dùng khác biệt framework
  để loại đối chứng gần nhất khỏi phân tích. NarraWorld là external-memory
  comparison riêng, không resource-matched recurrent baseline.
- Ít nhất một baseline hiện đại đủ đúng phương pháp (Gated DeltaNet hoặc RWKV-7)
  và causal Transformer. Token-shift GRU hiện có không được gọi full RWKV.
- Factorial: differencing versus learned-pair × factored versus flat/copy memory;
  cùng training recipe trước, recipe changes tách riêng. Nếu pair control thắng,
  không viết rằng sai phân tường minh có lợi.
- Hai điều kiện parameter-matched/state-byte-matched, thêm measured-cost nếu
  khả thi; không giả chúng tự trùng nhau.

**Bằng chứng cần cho một bài có sức ảnh hưởng:** lợi ích ở memory–quality frontier,
không chỉ một điểm tủ; ít nhất ba loại bài toán như prose narrative, dialogue
constraint changes và executable program-state descriptions; sources/test mới,
human audit; self-event/branch leakage; scaling theo K/horizon/divergence/rank;
nhiều seed và một quy mô lớn hơn sau khi đo máy thật. Không cần tất cả đều tăng:
failure map phải chỉ được khi nào nén residual mất tác dụng.

Phân tích lý thuyết chỉ được nhận khi assumptions đúng. Storage algebra không
phải theorem về reasoning; conditional error accumulation bound không tự chứng
minh LM ổn định. Cần cơ chế hoặc insight đủ mới ngoài tổ hợp các thành phần cũ.
**Dừng/redesign Q1** nếu shared prefix chỉ là cache optimization, bottleneck gây
loss lớn, routing cần gold, hoặc prior work đã thực hiện cùng thiết kế. Không
gắn nhãn high impact/high novelty trước khi qua các gate này.

## 8. Dữ liệu, đánh giá và đăng ký trước

Mỗi bài có test source riêng cho câu hỏi của mình; base corpus/tokenizer dùng
chung được công khai. Dữ liệu/weights đã dùng để chọn cấu hình không được giới
thiệu lại là fresh confirmation. Lưu run ID, corpus/tokenizer/source hashes,
training/selection budgets và provenance; citation đến công trình trước khi nó
thực sự tồn tại. Không đồng thời nộp nội dung trùng hoặc tái công bố bảng như mới.

Primary generator metric: tỷ lệ đoạn/cặp đáp ứng mọi mandatory propositions và
không mâu thuẫn; format 3–5 câu báo cả strict và semantic-only. Báo coverage,
changed/preserved, evasion, fluency, held-out PPL, từng seed. Với C báo new-event
rate, conditional và unconditional self-event success. Gold state dùng để score
ở inference, không đưa generator trong intrinsic condition. Primary scorer phải
được validated bằng nhãn thật; không mặc định revision evaluator trước đã hoạt động.

Cluster theo truyện nguồn/cặp, paired resampling cùng source giữa arms; seed
variation riêng. Preregister primary contrast và smallest useful effect sau
validation trước test; không chọn metric/seed theo dấu thuận. Hai người đọc mù
model/arm trên mẫu đại diện, nhãn trước phân xử, unclear và CI được giữ. Chưa có
nhãn người mới trong revision này. Mọi số mẫu/giờ gán nhãn là planning đến khi đo.

## 9. Venue và lịch có điều kiện

Ứng viên Q3 về CS/AI: J.UCS cho A/B/C khi có independent insight; Inteligencia
Artificial có thể phù hợp C/B nếu hạng ngành/index đáp ứng lúc nộp. Official
scope/fee statements đã tái mở ngày 25/11: [J.UCS](https://profile.jucs.org/),
[IBERAMIA](https://journal.iberamia.org/index.php/intartif/about).
Chính sách miễn phí chung chưa thay việc kiểm tra mọi phụ phí, độ dài và active
index. SJR/JCR/CiteScore giữ cột riêng trong khảo sát trước; chưa có fresh rank
verification đầy đủ trong lượt này. Không khẳng định Q3 CS từ Q3 Linguistics.

Ứng viên Q1: TACL nếu đóng góp NLP đủ rộng; JMLR chỉ khi principle/algorithm có
giá trị ML rộng, phù hợp [author scope](https://www.jmlr.org/author-info.html).
MIT Press liệt kê [TACL ở Diamond OA](https://mitpress.mit.edu/open-access-at-mit-press/journals/).
Đây là candidates, không acceptance/funding approval. Bản thảo không chứa tên
journal mục tiêu, quartile hay lời nói nó phục vụ bài khác. UEH eligibility và
nguồn tài trợ vẫn chưa được duyệt; ngân sách xuất bản cá nhân 0 VND.

Tháng 1: novelty/semantic/fluency gates và profile trước chia G; tháng 2–4: ba
pilot chạy luân phiên, dữ liệu/nhãn/đọc tài liệu song song; tháng 4–8: confirmation
có điều kiện và bản thảo độc lập, cộng 2–6 tuần sửa nội bộ mỗi bài. Lịch này có
thể dài hơn theo công sức nhãn; không hứa một tháng một bài. Ứng viên kiến trúc
được prototype sớm ở quy mô nhỏ; nghiên cứu chính có thể kéo dài 18–30 tháng.
Review time tách riêng, chưa biết; đủ bằng chứng thì nộp, không chờ milestone
của manuscript khác. Drafted/submitted/accepted/published đều chưa đạt.
