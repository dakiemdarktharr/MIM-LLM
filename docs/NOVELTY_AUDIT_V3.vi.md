# Novelty audit — revision 3, 25/11/2026

## Phạm vi và cách dùng

Tìm đối thủ để bác bỏ các claim dễ dãi, không tìm nguồn chỉ xác nhận ý tưởng.
Nguồn: arXiv/PDF pin version, ACL Anthology đã đọc trong lượt trước, PMLR,
NeurIPS/OpenReview proceedings, repo/trang lab tác giả và trang journal chính thức.
Không coi kết quả search/abstract hay một preprint là kết luận đã tái lập.

Lượt mới bắt đầu với **16 PDF**, bổ sung DASC và MoDr qua nguồn primary sau đó;
manifest ghi từng lần tải thành công/thất bại, hash và số trang. Đọc chọn lọc theo
bảng dưới, không nhận đã đọc toàn bộ các PDF. Tập 18 PDF của các lượt trước giữ manifest riêng.
Không cộng số record Undermind thành số bài đã xác minh. Các phiên bản đã pin
đều có ngày trước 25/11/2026 theo nguồn metadata được đối chiếu; current version
hay publication status khác với version tải thì phải ghi rõ.

Lượt Undermind mới đầu phiên chưa chạy vì free limit; tool báo reset 14:00 UTC,
21:00 Việt Nam. Đã đọc lại summary của search hoàn tất 24/11 để tham khảo, không
coi đó là kết quả search mới. Summary ấy dựa vào abstract/metadata và có lỗi phân
loại: Nested LSTMs có bản [ACML 2017 tại PMLR](https://proceedings.mlr.press/v77/moniz17a.html),
Latent Situations có bản [Findings ACL 2023](https://aclanthology.org/2023.findings-acl.795/).
Nguồn xuất bản gốc được ưu tiên hơn nhãn trong search summary.

Representative queries đã dùng (không phải toàn bộ query log của một systematic review):

- `language models recurrent memory counterfactual reversible state updates interference 2025 2026`
- `site:arxiv.org recurrent memory state delta supervision language model event updates 2026`
- `language model recurrent state tracking commutative updates invariance transition supervision 2025 2026`
- `"counterfactual" "no-op" "training" "language" invariant`
- `"language model" "counterfactual" "memory" "shared" "state" recurrent`
- `"recurrent" "counterfactual" "low-rank" memory`
- `"Differentiable Training Objective" "Counterfactual Story"`
- Title/ID lookup cho closest papers, official proceedings và author/lab pages.

Không đưa kết quả aggregator, blog/YouTube hay tin công nghệ vào bằng chứng kỹ
thuật. Không suy “chưa ai làm” từ một query không có hit. Đây là targeted audit,
không phải PRISMA/systematic review và không đo tình hình Việt Nam trong lượt này.

## Ma trận đối thủ quan trọng

| Key / nguồn chính | Tình trạng được xác minh | Phần đã đọc / cơ chế thực sự | Điều bị loại khỏi claim của chúng ta |
|---|---|---|---|
| [dto](https://arxiv.org/abs/2605.24885) | arXiv v1, preprint; chưa xác nhận venue | Abstract/Method III: objective khả vi từ score tương đối original/rewrite và semantic score; task là sửa kết thúc có reference. | A không thể nhận “đổi phần cần đổi, giữ phần còn lại” hay differentiable CF objective là mới. PDF ghi Amelie Girard; arXiv metadata ghi Amelia, cần đối chiếu trước bibliography cuối. |
| [cfi](https://arxiv.org/abs/2610.22942) | arXiv v1, preprint | §3 formulation/objectives: response/reward matching giữa invariant demographic prompt arms. | Invariance training trên open-ended responses đã có; A phải phân biệt no-op causal consequences với ép toàn prose không đổi. |
| [delayed](https://arxiv.org/abs/2609.32312) | arXiv v1, preprint | §2–3 và limitations: simulator QA sau token/write delays, disposable branches; chưa cô lập delay khỏi QA/EOS/additional compute, seed hạn chế. | B không phát minh delayed supervision; chỉ được nhận controlled result giải quyết confound nếu thực sự làm được. |
| [statewise](https://arxiv.org/abs/2610.33766) | arXiv v1, preprint | §3–4: typed state/tombstones, round-trip filtered self-training, relapse DPO; tracking tốt không tự dẫn tới obeying. | C không phát minh self-generated state supervision; probe accuracy không chứng minh continuation consistency. |
| [commitment](https://arxiv.org/abs/2606.05201) | arXiv v1, preprint | Abstract/introduction: persistent-state sufficiency và Counterfactual Erasure RL cho hidden computation versus committed state. | Không gọi bất kỳ train-time erase/commit loss nào là mới; khác narrative event memory nhưng cơ chế phải so kỹ. |
| [code](https://arxiv.org/abs/2602.14814) | arXiv v3; venue chưa xác minh ở lượt này | Abstract/introduction: code REPL traces với state reveals, probabilistic automata khi actions chưa fully observed. | NTP có state supervision và state reveal không mới; B phải vượt kết luận “RNN làm state tracking tốt”. |
| [bias](https://proceedings.mlr.press/v306/ebrahimi26a.html) | **ICML 2026**, PMLR 306 | Abstract/introduction và publication metadata; data efficiency của RNN/Transformer qua supervision regimes. | So hai backbone ở nhiều regime chưa đủ mới nếu chỉ lặp một ranking đã biết. |
| [stateicml](https://proceedings.mlr.press/v267/li25r.html) | **ICML 2025**, PMLR 267 | Task/abstract: permutation composition, associative scan và cơ chế state tracking; decoding/intervention framework. | Không nhận phát hiện latent state hay algebraic state tracking nói chung là mới. |
| [dagger](https://proceedings.mlr.press/v15/ross11a.html) | **AISTATS 2011**, PMLR 15 | Abstract/task rationale: học dưới phân phối observations do policy gây ra. | Roll-in training/exposure distribution có tiền lệ; C không được gọi frozen history bank là DAgger/on-policy algorithm. |
| [scheduled](https://proceedings.neurips.cc/paper/2015/hash/e995f98d56967d946471af29d7bf99f1-Abstract.html) | **NeurIPS 2015** | Abstract/introduction: giảm train/inference discrepancy bằng model-generated previous tokens theo curriculum. | Self-history training không phải khái niệm mới. Frozen semantic-event histories khác token scheduled sampling nhưng khác định dạng chưa đủ novelty. |
| [gdn](https://arxiv.org/abs/2412.06464) | **ICLR 2025**, đối chiếu proceedings PDF | Abstract và update-rule overview; gating kết hợp delta associative update. | “Có gate + delta” và modern recurrent memory không mới. Đối chứng cần implementation đúng, không token-shift toy. |
| [rwkv7](https://arxiv.org/abs/2503.14456) | arXiv version đã đọc; chưa audit venue riêng | Abstract/update-family metadata: generalized delta, vector gates, removal/insertion và expressive state tracking. | Hidden-state difference không đồng nhất delta-rule correction; không nhận tăng expressivity mà chưa chứng minh. |
| [kdn](https://arxiv.org/abs/2609.07816) | arXiv v2, preprint | Abstract/introduction: covariance/uncertainty-guided associative updates, diagonal/isotropic variants. | Một adaptive overwrite gate chưa tự là innovation mới; compare semantics/storage/uncertainty đúng cấp. |
| [eda](https://arxiv.org/abs/2606.26560) | arXiv v1, preprint | §3.2–3.3: erase direction khác write direction, rồi delta corrective write. | Không nhận erase/write separation là mới hoặc mô tả GDN là chỉ cộng vector. |
| [nestedlearning](https://proceedings.neurips.cc/paper_files/paper/2025/hash/4309616aaed8e848009bc4a7ef73b493-Abstract-Conference.html) | **NeurIPS 2025**; tải arXiv v1 sau conference | Abstract/proceedings metadata: nested optimization, self-modifying memory, continuum memory HOPE. | Nested Learning không phải Nested LSTM hoặc MIM-N→S; không đánh đồng tên “nested” thành cùng phương pháp. |
| [lowrank](https://arxiv.org/abs/2608.15156) | arXiv v4, preprint | Abstract/introduction: low-rank intervention-entry trong world model vật lý; compact entry không chứng minh closed low-dimensional dynamics. | Low-rank interface không mới; fixed residual subspace phải kiểm tra horizon/rank, không suy tự ổn định. |
| [dasc](https://arxiv.org/abs/2608.30386) | arXiv v2, preprint | Abstract/introduction: checkpoint compression theo retention horizon, zero fill hoặc suffix refresh khi reuse. | Prefix state compression đã có; phải đối chiếu học persistent residual qua từng token, không chỉ cache snapshot. Không trộn số liệu web abstract với PDF pin version khi chúng khác. |
| [modr](https://proceedings.iclr.cc/paper_files/paper/2026/hash/8a81180649011d1690e05c68bfeaa57c-Abstract-Conference.html) | **ICLR 2026**, official proceedings | Abstract/§3 overview: shared recurrent block, LoRA parameter branches, learned hard routing. OpenReview bị challenge/403; dùng proceedings primary. | Low-rank + branch + router không mới. State residuals khác parameter adapters, nhưng phải chứng minh giá trị chứ không chỉ đổi đối tượng được nén. |

Các hướng bổ sung sàng lọc ở mức abstract/author page, **không** tính là full-text
audit: [δ-mem](https://declare-lab.github.io/projects/online-memory/) có associative
state low-rank và nhiều matrices; [Professor Forcing, NeurIPS 2016](https://proceedings.neurips.cc/paper/2016/hash/16026d60ff9b54410b3435b403afd226-Abstract.html)
so training/sampling dynamics. TIME TRAVEL, PASTA, FactTrack, ConStory-Bench,
ChronoScope và CheckEval ở sổ nguồn trước vẫn là prior art bắt buộc.

## Phân loại khoảng trống, không gắn nhãn novelty cao trước kết quả

| Hướng | Khoảng trống dự kiến sau đối chiếu | Rủi ro | Cổng phải qua trước manuscript có kết quả |
|---|---|---|---|
| A | Tác dụng riêng của semantic no-op training so lexical controls/response matching trong generation qua nhiều updates. | **Cao**, gần DTO/CFI; thêm no-op chưa đủ. | Transfer và selective effects sau control chất lượng/lexical shift; insight hơn một metric được tối ưu trực tiếp. |
| B | Phân biệt semantic-write interference, token delay và label/format budget bằng thiết kế nhất quán. | **Trung bình–cao**, Delayed Supervision/code/bias đã rất gần. | Trả lời confound tài liệu đã nêu, có generation transfer và measured cost; không chỉ đổi seed/backbone. |
| C | Self-origin versus peer-origin frozen histories, kiểm soát độ khó/chất lượng và chấm theo lựa chọn thật. | **Cao**, tự sinh/self-training đã rộng. | Matching nguồn gốc đáng tin, error/acceptance yield, gain hoặc failure principle ngoài data-quality effect. |
| Architecture candidate | Shared fork snapshot + compact per-world recurrent residual, routed without state oracle, measured under memory budgets. | **Rất cao**, low-rank/multi-state/caching có tiền lệ; chưa chứng minh khoảng trống toàn ngành. | Vượt full state copies, same-byte unstructured bank, no-N/S, pair projection và modern recurrence; nhiều domains/scales, nontrivial memory-quality frontier. |

Nếu tìm thấy exact architectural match, thay cơ chế trước khi train lớn. Nếu
chỉ có “tổ hợp MIM + low-rank + router”, chưa có theory/empirical principle hơn
thành phần cũ, không nhận đó là high-novelty Q1. User muốn impact cao là tiêu chí
thiết kế; impact thực tế và editorial decisions vẫn là kết quả chưa xảy ra.

## Lượt Undermind mới đã hoàn tất và kiểm tra bổ sung

Sau reset 21:00 Việt Nam, search **Selective recurrent memory and state-consistent
generation** đã khởi chạy và hoàn tất ngày 25/11. [Search card và kết quả](https://app.undermind.ai/projects/ac70a7c0-70cf-4069-ad90-eb7860bbad1c?path=/Selective%20recurrent%20memory%20and%20state-consistent%20generation).
Search đưa ra **168 candidate records**, không phải 168 paper đã full-text verified.
Summary dựa abstract/metadata nhận ba khoảng trống training có điều kiện và yêu
cầu phân biệt persistent world residual với serving/counterfactual interfaces;
đây là gợi ý để kiểm tra, không chứng nhận novelty.

Đã lấy DOI/link cho bảy threats từ Undermind và mở lại arXiv gốc. Tải bổ sung
thành công SEED, TreeWY, NarraWorld, Flide, SchemaMem và Causal History Effects;
PDF From Simulation to Enaction timeout, chỉ dùng primary abstract/metadata cho
nguồn đó. Tổng lượt này: **24 PDF thành công**, một PDF bổ sung thất bại; không
tuyên bố đọc hết 24 bài. SEED đọc abstract và mô tả sink/factor update; TreeWY
đọc abstract/background; nguồn còn lại ở mức abstract/overview trừ khi có ghi khác.

| Nguồn mới, đều dùng như arXiv preprint | Threat thực sự | Sửa thiết kế sau đọc |
|---|---|---|
| [SEED](https://arxiv.org/abs/2611.06084), 04/11/2026 | Sink-plus-low-rank persistent recurrent state và cập nhật factors. | Q1 novelty chưa clear; cần compressed-state reference, không nhận low-rank update là mới. |
| [TreeWY](https://arxiv.org/abs/2608.20961), bản v2 trước ngày tra | Tree-structured GDN verification không full snapshot mỗi node. | Full-copy đơn giản chưa đủ; đối chiếu exact linear-rule branching khi áp dụng. |
| [Flide](https://arxiv.org/abs/2610.42148) | Exact forking cho attention/GDN decision branches. | Không nhận fork/cache sharing là novelty, tách predicted semantic routing khỏi engine metadata. |
| [NarraWorld](https://arxiv.org/abs/2609.32401) | External graph có facts, beliefs và hypothetical branches. | Không nhận possible-world narrative memory là mới; external system khác intrinsic state. |
| [From Simulation to Enaction](https://arxiv.org/abs/2605.25459) | Nhận on-policy histories, surprise điều chỉnh entropy. | C cần frozen-learner surprisal matching/strata; không nhận giảm entropy là memory improvement. |
| [Causal History Effects](https://arxiv.org/abs/2609.05882) | Can thiệp assistant text ảnh hưởng hành vi sau. | C phải kiểm định training provenance ngoài quality/history effects đã biết. |
| [SchemaMem](https://arxiv.org/abs/2609.33436) | Schema-indexed selective updates và delayed retrieval. | B là schedule/confound study; không là đầu tiên học state retrieval. |

Crossref và OpenAlex đã được query qua API primary với cụm
`counterfactual recurrent state memory language models`, mỗi nguồn lấy ba record.
Đây là metadata screening nhỏ: có record ngoài scope, trùng work/version và kết
quả ngày chưa đủ kiểm chứng; không dùng làm positive evidence cho khoảng trống.
Response và URL query lưu trong metadata-searches.json cục bộ. Không gọi sáu
record đó là sáu công trình gần đã đọc. Không quét toàn bộ Crossref/OpenAlex.

**Kết luận audit:** không có căn cứ tuyên bố cả bốn hướng đã đạt novelty cao.
Thiết kế đã thu hẹp claim và tăng đối chứng; A/B/C vẫn cần independent empirical
insight, Q1 phải vượt SEED/fork/compression baselines và có đóng góp cơ chế vượt
tổ hợp. Nếu không, đổi kiến trúc hoặc dừng claim Q1 trước long training.
