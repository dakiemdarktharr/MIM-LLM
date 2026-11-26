# Q3-A: kiểm tra tài liệu bổ sung ngày27/11/2026

Trong lúc foundation chạy, tra Undermind trong workspace MIM-LLM bằng query:
“We train autoregressive language models to distinguish counterfactual
interventions that change a story outcome from semantic no-op edits that
preserve it. We compare paired data augmentation with matched irrelevant
numerical perturbations and evaluate jointly correct free-text continuations,
state consistency, and invariance under multiple blocking conditions.”

Giới hạn semantic search6records, published_until2026-11; không systematic
review. Hai deep searches cũ đã hoàn tất được giữ, không chạy lại hoặc tính
6records thành6bài đọc toàn văn. Bốn hồ sơ được đối chiếu thêm với nguồn chính;
DTO đã có trong audit cũ, không đếm là phát hiện hoàn toàn mới.

| Nguồn | Mức đã kiểm ngày27/11 | Ý nghĩa cho thiết kế |
|---|---|---|
| [Training Objectives and Evaluation Metrics for Counterfactual Story Rewriting](https://doi.org/10.1145/3785019) | Undermind abstract; Crossref metadata qua [API](https://api.crossref.org/works/10.1145%2F3785019): Amelie Girard, Inigo Jauregi Unanue, Massimo Piccardi; ACM/TALLIP journal-article, online6/3/2026. Trang ACM trả403; chưa đọc toàn bài. Ngày10/2 từ aggregator không thay ngày Crossref. | Cần đối chiếu objective/metric chọn lọc trước claim mới; không khẳng định đã tái lập hoặc xác minh kết quả từ abstract. |
| [DTO,arXiv2605.24885v1](https://arxiv.org/html/2605.24885v1) | Đọc thêm các đoạnIII-A–E,AppendixB; preprint24/5/2026, chưa xác nhận venue. | Delta-score so similarity với reference sửa và ending gốc; soft embeddings qua scorer. Không tự là oracle logic. Objective khả vi/giữ phần không đổi không phải novelty của A. |
| [Counterfactual Story Reasoning and Generation](https://aclanthology.org/D19-1509/) | Trang/abstract/BibTeX ACL2019; chưa đọc lại toàn PDF ở lượt này. DOI10.18653/v1/D19-1509; trang5043–5053 theo ACL, khác aggregator5042–5052. | TimeTravel đã đặt mục tiêu chỉnh phần hậu quả và giữ phần bất biến. Không nhận dạng mục tiêu này là mới. |
| [Counterfactual Token Generation in Large Language Models](https://proceedings.mlr.press/v275/chatzi25a.html) | PMLR metadata/abstract: CLeaR2025,275:1291–1315. Undermind ghi2024 do preprint2409.17027. Chưa đọc toàn PDF ở lượt này. | Gumbel-Max SCM/counterfactual token sampling không phải MIM hidden-state differencing; cùng seed thông thường chưa tái lập cơ chế ấy. |

Về DTO: forward qua soft embedding và scorer khác tối ưu trực tiếp mệnh đề
logic. Bài dùng Gumbel-softmax và BART; AppendixB nêu A40/48GB. Không thêm
scorer lớn vào matched-budget study mặc định; nếu adaptation phải ghi chi phí
và khác biệt objective. Không sao chép claim “unbiased” cho discrete-generation
objective chỉ nhờ có gradient qua relaxation; đó cần chứng minh riêng.

## Quyết định cho A — thiết kế, chưa là kết quả

Giữ câu hỏi A1−A2 hiện hành và gate stop/merge. Không lấy CE/JS, đổi dataset,
quy mô nhỏ hoặc free prose riêng lẻ làm novelty. Trước primary post cần chốt
thách thức boundary/multiple-blocker hoặc giới hạn claim rõ, transfer có quyền
dùng, human audit và so với giải thích đơn giản do exposure/format/number edits.
Nếu chỉ có template exposure benefit, không hứa đủ một manuscript độc lập.

Phân biệt **đổi tiền đề trong văn bản** với **counterfactual token generation
trong một SCM**. Các cặp Q3-A được chấm theo hệ quả quy tắc đã khai báo. Cùng
seed17 cho base/effective/no-op là decoding control; không chứng minh đã suy ra
exogenous noise hay có coupling phản thực tế đúng theo Gumbel-Max. Không dùng
thuật ngữ causal identification cho phép so sánh này. Backend FP64 giải một
lỗi số học, không tạo thêm novelty khoa học.

Không đổi source/data/plan của foundation đang chạy, không thêm arm/optimizer,
không chọn test hoặc viết manuscript có kết quả trong lượt tra này.

## Bổ sung sau khi foundation seed 0 hoàn tất

Đã lookup DOI bài journal qua Undermind (`Gir26b`), kiểm thêm metadata cơ quan
UTS và thử nguồn publisher. Undermind không có PDF; public PDF endpoint trả
403 và browser dừng ở security verification. Không giải/bypass challenge;
phạm vi đọc bài journal vẫn metadata/abstract.

Footnote của preprint DTO dẫn tới repo tác giả. Đã đọc source có pin, kiểm
12 file/90.956 bytes với Git blob SHA1 và SHA256, không chạy/import upstream
code hoặc tải weights/data. Snapshot triển khai đường DTO-Score có clamp,
không phải bằng chứng đã tái lập cả ba biến thể hoặc từng bảng trong paper.
Chi tiết về source scope, gradient qua frozen scorer, vocabulary/mask/cost và
quyết định giữ A1−A2 tại [audit code tác giả](Q3_A_DTO_AUTHOR_CODE_AUDIT_20261127.vi.md).
Receipt: `configs/q3a/dto_author_code_audit_20261127.json`.

Đây là tiến bộ về đối chiếu phương pháp, chưa hạ mức rủi ro novelty hoặc thay
thế transfer/primary/human evidence. Nguồn LaTeX đã cập nhật trạng thái thật
của pilot và kết quả validation âm; không compile hoặc nhận là manuscript
hoàn chỉnh có kết quả chính.

## Phạm vi dữ liệu được xác nhận bằng audit train

[Audit quy tắc](Q3_A_RULE_SUPPORT_AUDIT_20261127.vi.md) đã kiểm đúng 6.000 nhóm
train: không có điện về đúng hạn hoặc hai blocker đồng thời ở cả bốn role.
Các cặp no-op hiện tại giữ mọi fact được theo dõi. Ví dụ toán học giữ hành
động chờ nhưng đổi tình trạng điện cho thấy phải tách invariance theo từng
mệnh đề. Probe thật từ chối ép invariant lên target đã đổi; đây là kiểm
contract, không phải model đã giải được bài. Không đọc controlled test hoặc
đăng ký challenge mới. Mức rủi ro novelty và quyết định stop/merge vẫn giữ.
