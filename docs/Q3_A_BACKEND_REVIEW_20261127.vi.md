# Quyết định backend trước lượt5 — 27/11/2026

Quyết định kỹ thuật dựa trên chẩn đoán **sau khi phát hiện lỗi**, không phải kết
quả khoa học đã preregister. Giữ nguyên mọi strict-logit fail trước đây. Không
đổi dữ liệu, targets, optimizer, learning rate, model, seed hoặc quyền train.

Đã đọc lại độc lập precision report SHA
`b970e26a7940a58f223796a6f5380679e5de92f06bd003b8253683e72c518e7b`,
gắn checkpoint3d0328…/70.895.155LM targets. Source diagnostic SHA
`f9a40353f1a59e2cd01ac222b3d93c53c26a75b7f735cfaaa7d504f0756ef5df`.

- Tắt MHA inference fastpath: train-features/dense eval khớp exact0 trong panel
  đã đo, thay sai khác lớn tới0,036 của default inference.
- FP64 CPU từ cùng FP32 weights: hai case641/1024 pass1e-10, max path error
 4,369837824924616e-13; causality/reset exact0.
-2789valid positions,4production paths:0argmax mismatches so với FP64. Max full
  softmax L1=6,217517905633884e-5; max temperature0,8/top-k40 policy L1=
 8,604755116236001e-5. Đây là phân phối tại **cùng context đã kiểm**, không
  bảo đảm toàn bộ sampled continuation sẽ giống nhau hoặc sampler bitwise.
- Batch train thật1024targets: loss cả hai flag=2,405290126800537; toàn bộ
  parameter gradients bitwise bằng nhau. Không optimizer update; weight và
  checkpoint hashes không đổi. Đây là kiểm một batch, không đo loss khoa học.

Sai khác FP32 nhỏ của token-step vẫn chưa đạt strict-logit gate cũ theo mọi
vị trí; không đổi tên report đó thành pass. Bằng chứng FP64/phân phối/gradient
cho phép tiếp tục feasibility với backend đã kiểm và giới hạn engineering
công khai. Không suy từ đó model viết tốt, có lợi íchA1−A2 hoặc đủ chuẩn journal.

## Contract áp dụng tới checkpoint tiếp theo

`configs/q3a/foundation_backend_policy.json`, policy ID
`4ee4ddd2fc93406eed8df2ae10eb08339b59ba8b8795ae169cf57ace9a48ddc9`:
MHA fastpathFalse; FP64 path agreement1e-10;0argmax mismatches; cả full và decode
policy L1≤1e-4; same-weight hashes và tested loss/gradient equality; panel cố định
641/1024. Giới hạn L1 là engineering choice công khai sau chẩn đoán đầu tiên;
phải giữ nguyên trước checkpoint mới, không nới sau khi fail. Không thay chỉ số,
sample hoặc split của thí nghiệm khoa học. CPU FP32strict report vẫn fail.

Launcher mới `scripts/run_q3a_foundation_reviewed.py` kiểm policy/proof/current
Drive và scratch checkpoint hashes, source diagnostic, old ledger terminal;
ghi backend receipt trước gọi **cùng driver V4**. Tắt fastpath trong child
process thật, không chỉ trong notebook parent. C18foundation source/fingerprint
không đổi. Driver V4 vẫn enforce16slots/1100s/16CUdrop/currentUI và exact plan/run
permission. Launcher không tự chạy primarypost hoặc mở seed khác/test.

4gate tests gồm stale checkpoint, gradient disagreement, NaN/Inf/excess drift và
threshold relaxation rejection;2probability metric tests; default suite
216passed/18trainingdeselected. Actual cloud report cũng đã được gate kiểm lại
local. Không dùng fixtures làm scientific receipt.

Chưa launch5 tại thời điểm viết quyết định. Phải kiểm UI/resources/hash hiện
tại trước launch và audit archive mới sau driver. Nếu checkpoint sau vượt
contract, dừng mở rộng và điều tra; không chạy đi chạy lại để tìm receipt đẹp.
