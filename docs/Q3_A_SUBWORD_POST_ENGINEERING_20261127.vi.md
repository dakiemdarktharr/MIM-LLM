# Chuẩn bị post-training subword — 27/11/2026

Các module plan/runner mới chưa tạo plan thực hoặc cấp quyền cho primary run.
Foundation c18 và các source fingerprint của nó giữ nguyên. Template 24 runs
là 4 arms × 2 backbones × 3 seeds; đòi 6 foundation parents thực, mỗi post seed
dùng đúng foundation seed. Hai seed0 feasibility parents chưa đủ để chạy ma trận.

Plan kiểm hashes của tokenizer/data/parents, archive audit đủ từng stage,
writing-feasibility evidence và source. Test chỉ byte-hash để kiểm toàn vẹn,
không parse/tokenize/generate/score. Writing gate phải gắn đúng cả hai seed0
parents và bằng chứng được kiểm lại khi load; một JSON marker tự nó không
chứng minh chất lượng khoa học hoặc nhãn người.

Runner dùng fresh AdamW từ parent, response-only next-token CE; A3 thêm JS
trên component probes train, xoay 5 loại. Probes là auxiliary training task,
không thay output truyện tự nhiên. Ghi target/input/probe exposures, optimizer,
RNG, cursor, time, loss, gradient, checkpoint và validation diagnostic. Chọn
final checkpoint theo đúng target budget, không chọn theo test hoặc loss đẹp.

Hai synthetic CPU optimizer/resume tests cho minGRU và Transformer đã pass:
77 targets, CE+JS, uninterrupted so với resume có model/optimizer tensors và
counter khớp bitwise. Tokenizer fixture cố định, không fit. Đây là engineering
test, không phải parent khoa học 100M targets hoặc primary result.

Default suite hiện **206 passed,18 training tests deselected**; 5 plan tests
nằm trong suite này. Ruff của bốn file mới pass. Policy chỉ bổ sung chính xác
hai synthetic test IDs; chưa cho phép các real subword-post IDs hoặc seeds mới.

Còn thiếu trước primary launch: measured whole-study budget/orchestrator,
generation/evaluation/selection adapters, evidence gate thật, sáu parents,
analysis preregistration được hoàn tất và quyết định novelty/transfer theo
protocol. Không gọi pipeline này hoàn chỉnh hoặc sẵn sàng primary training.
Template giữ budget null và trạng thái draft_not_authorized.
