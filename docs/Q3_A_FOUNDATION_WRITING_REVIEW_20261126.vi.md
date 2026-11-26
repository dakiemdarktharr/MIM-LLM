# Bộ mẫu viết cố định sau foundation — 26/11/2026

Đây là công cụ chuẩn bị, chưa phải kết quả sinh văn bản hoặc bằng chứng đạt
writing gate. Hai baseline foundation không chứa MIM và không được gọi là mô
hình chat hoàn chỉnh. Không thay tiêu chuẩn hoàn tất Q3-A bằng kết quả unit test.

`scripts/review_q3a_foundation.py` có hai lệnh tách biệt:

```powershell
.venv/Scripts/python.exe scripts/review_q3a_foundation.py prepare --plan configs/q3a/foundation_plan.json --recipe configs/q3a/reference_inference_recipe.json --corpus data/raw/q3a-foundation-20261126.jsonl --output artifacts/q3a-foundation-20261126/writing-review-v1.json
# Chỉ chạy generate SAU khi cả hai foundation final.pt đủ LM+SFT thực tế:
.venv/Scripts/python.exe scripts/review_q3a_foundation.py generate --plan configs/q3a/foundation_plan.json --manifest artifacts/q3a-foundation-20261126/writing-review-v1.json --checkpoint-root LOCAL_OR_DRIVE_RUNS --output PRIVATE_NEW_DIRECTORY --device cpu
```

`prepare` đã thực thi trên corpus đã khóa hash, không tạo model, fit tokenizer,
cập nhật optimizer hoặc chấm test. Manifest riêng tư chứa đủ16source IDs/prefixes
đã dùng trong chẩn đoán cũ; mỗi prefix phải khớp SHA trong recipe cũ và thuộc
validation. Thiếu/trùng/sai split/sai prompt thì dừng, không thay truyện khác.
Thêm đúng một prompt unconditional ở dạng đã học. Giữ T0,8/top-k40/seed17,
max128BPEtoken và kiểm context không cắt/drop prompt. Không chọn seed giải mã
sau khi xem output. Manifest/private prompts không đưa GitHub.

`generate` kiểm **cả hai** parent trước khi phát ra bất cứ mẫu nào: đúng plan,
run, FP32, complete, stage2, stage_targets0, tổng100Mtarget và updates>0.
Không dùng checkpoint mới học LM một phần để gọi là nền hoàn tất. Kiểm nguồn
implementation/manifest/decoding/tokenizer, hash checkpoint trước và sau đọc,
load state dict strict. Một panel thành công chứa34samples (17/model), kể cả
EOS sớm, chuỗi trống, lặp hoặc chạm giới hạn. Mỗi hàng có run/plan/review/checkpoint
hash, tham số thực, seed và diagnostic flags. Ghi/flush từng hàng; lỗi để lại
partial JSONL và **không** có completed receipt. Không ghi đè thư mục output.

Số chuỗi khác nhau, số EOS/cap/empty chỉ là chẩn đoán; không phải điểm độ trôi
chảy, logic hoặc nhãn người thật. `human_label` luôn null, `primary_evaluation`
false, `writing_gate_passed` null. Người đọc còn phải xem đủ mẫu về3–5câu,
bám prefix, tự tạo/nhớ sự kiện, mâu thuẫn và né viết chung chung. Hiện chỉ có
người dùng làm reader; không báo inter-rater agreement hoặc independent human
validation nếu chưa có người thứ hai. Chưa có nhãn người thật.

Bốn kiểm tra không optimizer đạt: nguyên vẹn lịch sử16prefix/test fallback;
không bỏ quaSFT/checkpointpartial; ràng buộc manifest/decoding; chạy end-to-end
34outputs **trên fixture tổng hợp nhỏ** và chặn parent thứ hai chưa hoàn tất.
Toàn suite193passed/16training deselected. Output fixture trong pytest temp
không phải kết quả khoa học, không thay panel thực trên checkpoint đã train.

Phần primary subword post-training runner/plan/đánh giá và phép phân tích đăng
ký vẫn còn phải hoàn tất. Không mở A0–A3/test/B/C/Q1/LaTeX nhờ receipt này.

## Cập nhật xác thực

CPU-only Drive refresh thực tế hoàn tất lúc2026-11-26T14:25:09Z,0optimizer,
0driver reservations; receipt191bytes được đọc lại qua Drive connector. UI
xác nhận0active sessions/rate0/balance596,66 sau release. Quyền Drive hiện đã
hoạt động; yêu cầu xác minh danh tính trước đó là lịch sử. L4 yêu cầu sau đó
được UI báo1session/rate2,33 vào khoảng21:31 giờ Việt Nam, kernel còn đang
kết nối ở lần quan sát tiếp; không gọi đây là profile đã chạy hay train mới.
