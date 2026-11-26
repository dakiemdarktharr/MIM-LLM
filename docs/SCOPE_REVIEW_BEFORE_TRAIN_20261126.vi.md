# Scope chốt trước lượt train đầu — 26/11/2026

Quyết định dựa trên targeted prior-art review và kiểm tra thiết kế, không phải
ước lượng xác suất được nhận. Người dùng đã cho phép bắt đầu Q3-A trên Colab
Pro+ và lưu Drive. B/C/Q1 chưa được cấp lệnh train trong lượt này.

## Quyết định cho từng bài

| Bài | Scope giữ lại | Sửa/cổng bắt buộc để có đóng góp độc lập |
|---|---|---|
| A | Học sử dụng thay đổi điều kiện liên quan nhưng giữ nguyên hệ quả; đồng thời phải phản ứng đúng khi hệ quả thực sự đổi. | **Thay A2 punctuation bằng numeric nuisance-clock control**: tất cả prompts có một đồng hồ bảo tàng không liên quan, khởi tạo độc lập; A2 đổi đúng đồng hồ đó, A1 đổi thời điểm điện về trong cùng decision region. Khớp byte length, số ký tự sửa, source order và reference targets. Còn khác vị trí/ý nghĩa nên không nhận pure causal identification. |
| B | Tác dụng của semantic interference so với token distance trong delayed supervision, đo chuyển sang viết đoạn văn. | Delay/QA/disposable branches là prior art. Bài chỉ có giá trị nếu phân giải confound delay/write/prefix-compute và generation transfer hoặc failure principle có độ chính xác hữu ích; giữ counterbalance và separate target/compute accounting. |
| C | Controlled roll-in input distributions và consistency theo actual generated event. | Chín mẫu grammar chỉ đủ làm pilot kiểm soát. Không đủ làm bằng chứng standalone rộng nếu không có free-run/naturalistic transfer hoặc insight vượt quality/surprisal selection. Không gọi frozen bank là on-policy; không diễn giải origin metadata thành nguyên nhân độc lập. Thiếu overlap hoặc input collapse thì dừng. |
| Q1 | Cơ chế MIM-based persistent branch state, chất lượng/bộ nhớ khi duy trì nhiều thế giới. | Low-rank memory và exact forking đã có. Cần giá trị riêng so full copies, SEED-style compression+forking, same-byte state, learned pair projection, bỏ N/S và modern recurrence; route không oracle; nhiều domain/horizon/scale. Chưa triển khai hoặc chứng minh novelty/impact. |

Giữ các bài standalone và phân bổ post-training/selection ngang nhau. Tái sử
dụng shared initialization phải công bố; không trình bày lại cùng phát hiện như
mới. Mục tiêu chat MIM-LLM vẫn cần general language learning, instruction/chat
fine-tuning và multi-turn evaluation riêng.

## Vì sao thay A2 trước train

Punctuation-only control trước đây khớp lượng sửa nhưng yếu về loại token và
nội dung. Numeric control mới thay một thời điểm khác, với +1 phút và cùng số
ký tự thay đổi như no-op điện. Museum-clock time được lấy mẫu độc lập có điều
kiện trên edit count, không sao chép power time. Base/effective/no-op giữ clock
đó cố định; surface-role chỉ đổi clock và không đổi decision target. Tên role
`surface` được giữ cho tương thích schema, không còn mang nghĩa punctuation.

Không tăng số arm hoặc budget. A1−A2 nay kiểm tra task-relevant versus irrelevant
decision-preserving variation, không chứng minh mọi semantic no-op hoặc mọi
paraphrase. Pilot controlled templates còn cần nguồn/linguistic phenomena mới,
shortcut audit, writing/coverage và real blinded readers trước broad claim.
Nếu hiệu ứng chỉ thuộc vị trí clock/template thì thu hẹp, gộp hoặc dừng.

## Nguồn và độ sâu kiểm tra

Ngày tra26/11/2026. Tái dùng search Undermind hoàn tất25/11 (168 candidate
records, **không** phải168 full-text verified papers):
[Selective recurrent memory and state-consistent generation](https://app.undermind.ai/projects/ac70a7c0-70cf-4069-ad90-eb7860bbad1c?path=/Selective%20recurrent%20memory%20and%20state-consistent%20generation).
Đọc lại primary HTML các phần task/method liên quan và limitations của:

- [DTO](https://arxiv.org/html/2605.24885v1): counterfactual rewriting, fidelity và source consistency. Không nhận minimal-change objective là mới.
- [Aligning Language Models Towards Counterfactual Invariance](https://arxiv.org/html/2610.22942v1): matched prompts, relevance và response/reward matching; A3 là adaptation, không objective mới.
- [Delayed Supervision](https://arxiv.org/html/2609.32312v1): delayed QA/disposable branches; B không phát minh chúng.
- [From Simulation to Enaction](https://arxiv.org/html/2605.25459v1): on/off-policy histories, surprise/entropy; C không lấy giảm entropy làm consistency.
- [StateWise](https://arxiv.org/abs/2610.33766): primary abstract/metadata, typed-state training là tiền lệ.
- [SEED](https://arxiv.org/abs/2611.06084) và [Flide](https://arxiv.org/abs/2610.42148): primary abstract/metadata đối chiếu compression/forking; không tái lập hoặc full-text audit mới.

Các nguồn2026 trên được dùng dưới trạng thái arXiv/preprint; không suy venue
review từ arXiv DOI. Không có search exhaustive mới, khảo sát Việt Nam mới hoặc
xác nhận fee/quartile/funding mới. Không có cơ sở gán xác suất acceptance.

## Lượt train và metric

Initial session chặn ở warm-up seed0 của hai backbone, soft wall cap20phút
cho tiến trình GPU. Sau đó xem validation writing rồi mới mở matched A1/A2
pilot; chưa phát toàn bộ24post jobs. Không tự mua thêm CU. Pipeline ghi mỗi
update: UTC, CE/JS/objective, gradient norm trước clip, LR, targets/input/probe
tokens, cursor/epoch, seconds, throughput và peak VRAM. Validation lưu CE/PPL,
denominator/corpus/time riêng. Run metadata gồm software/GPU, config/data/plan
hash, parent/checkpoint hashes, optimizer/RNG/cursor trong checkpoint.

Checkpoint local mới được copy sang Drive qua file tạm, đọc lại đối chiếu SHA
rồi thay bản latest; giữ một bản previous. Không khẳng định rename trên Drive
là giao dịch toàn cục. Run/validation/environment/sync logs giữ cùng session;
metric writing/logic phải lấy từ output và human labels thật, không sinh nhãn
để lấp bảng. Test vẫn khóa. Đây là exploratory feasibility, chưa final result.
