# Q3-A: đối chiếu mã DTO của tác giả — 27/11/2026

Đây là đọc nguồn có pin và một kiểm tra công thức trên scalar giả lập, **không
phải tái lập thí nghiệm DTO**. Không chạy/import code tác giả, tải weights/data,
train, sinh mẫu mới, gán nhãn người hoặc mở test của dự án.

## Phạm vi và nguồn

Undermind workspace MIM-LLM được dùng để lookup chính xác DOI
`10.1145/3785019`, cite key `Gir26b`; PDF được trả là unavailable. Một truy vấn
web theo nguyên title dẫn tới [hồ sơ cơ quan của đồng tác giả](https://profiles.uts.edu.au/Inigo.JauregiUnanue/publications).
Trang này xác nhận title, ba tác giả, journal/volume và ngày hiển thị 6/3/2026.
Undermind ghi 10/2/2026; giữ riêng hai trường ngày, không tự giải thích sự khác
biệt. Với bài journal này, vẫn chỉ đọc metadata/abstract; không tuyên bố đã
kiểm phương trình hoặc kết quả từ toàn văn.

Nguồn code là một công trình khác cùng hướng:
[DTO, arXiv v1](https://arxiv.org/html/2605.24885v1), preprint ngày 24/5/2026.
Footnote ở Introduction liên kết trực tiếp repo
`amelie-girard7/TimeTravel-DifferentiableMetrics`. Pin commit
**`a8a6d049d1128d99f5cb1873bcee93ef1075d526`**, tree
`29a9be53f113eb46ec7f9a392024b446418b7dd2`; metadata commit ghi 23/7/2025.
Đây không phải bằng chứng mỗi bảng trong paper dùng chính snapshot này.

GitHub connector kiểm metadata/tree và 12 file; tải riêng tổng **90.956 bytes**
để đọc, đối chiếu cả Git blob SHA1 và SHA256. Root có MIT license; phần
BARTScore vendored có Apache-2.0 riêng. Không clone toàn repo hoặc đưa source
tác giả vào package của MIM. File được hash-verified không đồng nghĩa mọi file
đã được đọc toàn bộ: đọc chọn phần call graph liên quan và giữ rõ phạm vi.
Không đếm 12 file thành 12 bài nghiên cứu.

## Cơ chế đã xác minh ở snapshot

| Thành phần | Quan sát từ nguồn chính | Hệ quả khi so sánh |
|---|---|---|
| [DTO model](https://github.com/amelie-girard7/TimeTravel-DifferentiableMetrics/blob/a8a6d049d1128d99f5cb1873bcee93ef1075d526/src/dto/models/model.py) | Logits đi qua Gumbel-softmax, rồi nhân với embedding matrix của scorer. `dto_loss_embeds` tính cả điểm edited/original nhưng giá trị trả chỉ là âm mean edited score. | Đây là đường **score-only**, tương ứng DTO-Score/Eq.6; không coi việc không dùng original term là lỗi so với biến thể đó. Snapshot này chưa đủ để tái lập DTO-Delta và Score+Delta. |
| [Metric wrapper](https://github.com/amelie-girard7/TimeTravel-DifferentiableMetrics/blob/a8a6d049d1128d99f5cb1873bcee93ef1075d526/src/dto/utils/metrics.py) | Scorer ở eval, parameters được freeze; nhánh train vẫn cho gradient qua input embeddings, nhánh validation tắt gradient. | Freeze weights không đồng nghĩa tắt gradient theo input. Khi port phải kiểm gradient thực đến generator, không chỉ nhìn `loss.requires_grad`. Chưa đo gradient của BART trong audit này. |
| [BARTScore implementation](https://github.com/amelie-girard7/TimeTravel-DifferentiableMetrics/blob/a8a6d049d1128d99f5cb1873bcee93ef1075d526/src/BARTScore_metric/bart_score.py) | Nhánh soft-embedding tính negative NLL chuẩn hóa theo target length, clamp score vào [-3; -0,5]; encoder mask tạo toàn số 1. | Cần phân biệt score đã clamp với raw metric, và khai báo soft-sequence length/mask. Không tự xem soft inputs là một đoạn sinh rời rạc đã kết thúc bằng EOS. |
| [Config](https://github.com/amelie-girard7/TimeTravel-DifferentiableMetrics/blob/a8a6d049d1128d99f5cb1873bcee93ef1075d526/src/dto/utils/config.py), [train entry point](https://github.com/amelie-girard7/TimeTravel-DifferentiableMetrics/blob/a8a6d049d1128d99f5cb1873bcee93ef1075d526/src/dto/train_dto.py) | Dùng pretrained BART generator và BART scorer; default snapshot có Gumbel temperature 1, hard=False, annealing=False. Callback chọn theo validation DTO loss. | Đó là thiết kế objective/selection khác nghiên cứu từ đầu của ta. Chưa profile phần cứng hoặc xác minh cấu hình sinh từng bảng; không suy ra runtime/cost của máy mình từ config. |

Trong ký hiệu riêng cho việc đọc code, nếu \(a_i\) là score đối với reference
edited, đường loss ở snapshot là \(-N^{-1}\sum_i\operatorname{clip}(a_i,-3,-0.5)\).
Kiểm công thức bằng ba scalar giả lập -4, -2, -0,25 cho gradient của tổng loss
lần lượt **0, -1, 0**. Đây chỉ xác nhận bão hòa của phép clamp ngoài miền;
không phải đo tỉ lệ gradient bằng 0 khi train BART hoặc phản bác kết quả paper.

Paper trình bày cả score, delta và score+delta; soft embeddings là relaxation
của đầu ra rời rạc. Không suy ra một gradient unbiased cho expected discrete
quality chỉ từ việc loss khả vi. Mục tiêu minimal rewriting đã có từ trước,
không phải novelty mới của Q3-A.

## Quyết định thiết kế của dự án, chưa phải kết quả

Giữ **A1−A2** là đối chứng chính đã chuẩn bị. A3 của ta là JS trên các vị trí
câu trả lời probe chuẩn, gồm EOS, dưới teacher forcing; nó không phải DTO,
full CSR hoặc một bảo đảm cho phân phối đoạn văn sinh tự do. Mỗi cách đều cần
được đánh giá ngoài loss tối ưu, với coverage, sự kiện cụ thể, contradiction
và kiểm tra người đọc trên continuation thật.

Không thêm DTO thành arm thứ năm mặc định trước feasibility. Full DTO dùng
pretrained generator/scorer và thông tin/compute khác. Chưa đo tài nguyên trên
máy ta; không được gọi nó cost-matched hoặc dùng cùng ngân sách đã đo cho hai
model nhỏ. Nếu sau này cần adaptation, phải ghi rõ scorer, nguồn pretrained,
vocabulary alignment, soft length/mask, clamp, gradient check và chi phí.
Tokenizer GPT-Neo frozen của ta không tự có token IDs tương ứng với BART;
không được nhân vector xác suất với embedding rows chỉ vì kích thước gần nhau.

Đóng góp A vẫn phải là insight thực nghiệm về selective consequences vượt
numeric nuisance/exposure và có failure/transfer evidence. Đổi backbone, dùng
quy mô nhỏ, thêm một divergence hoặc dùng code khác không tự chứng minh tính
mới. Giữ điều kiện thu hẹp/gộp/dừng. Mã/source/data/rule của foundation c18 và
34 output thật không thay đổi trong lượt đọc này; nhãn tác giả vẫn chờ.

Receipt: [`dto_author_code_audit_20261127.json`](../configs/q3a/dto_author_code_audit_20261127.json).
