# Q3-A: công sức nhãn người trước khi khóa test

Ngày26/11/2026. Plan hiện hành:
`ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142`.
Đây là phép tính **dự kiến**, không phải thời gian gán nhãn đã đo hoặc power analysis.

## Quy mô thực của ma trận

Có24post runs:4arms×2backbones×3trainingseeds. Primary A1/A2 gồm12runs;
mỗi nguồn có3outputs(base/effective/noop) cho mỗi run và một decoding seed.
Warm-up checkpoints không được tính như generator so sánh độc lập.

Giả sử2reader độc lập và **2phút/output/reader**:

| Source clusters | Outputs primary A1/A2 | Giờ-người primary | Outputs cả4arms | Giờ-người cả4arms |
|---:|---:|---:|---:|---:|
|12|432|28.8|864|57.6|
|24|864|57.6|1728|115.2|
|48|1728|115.2|3456|230.4|
|96|3456|230.4|6912|460.8|
|400|14400|960|28800|1920|

Chưa gồm đào tạo reader, audit nguồn/semantics, adjudication hoặc transfer tự
nhiên. Ví dụ400sources×3sentences không phải1200mẫu độc lập. Tính từ plan bằng
`scripts/plan_q3a_annotation_load.py`; thay thời gian giả định sau pilot người thật.
Không giảm cỡ mẫu rồi gọi precision/power vẫn giữ nguyên.

## Protocol trước test

1. Pilot rubric trên **validation**, có2người thật và provenance/consent phù hợp.
   Đo thời gian, ambiguity, disagreement và mức hiểu rubric; không chấm từ arm ID.
2. Chốt smallest useful effect và precision/power ở cấp source. Dùng pilot
   variance và mức nguồn lực thật; không chọn n từ kết quả test hoặc số câu.
3. Đăng ký source strata, sampling seed và toàn bộ nguồn/pairs/systems trước
   final-test generation. Giữ tất cả trainingseeds cho primary contrast.
4. Có thể ưu tiên nguồn lực cho primary A1/A2; secondary A0/A3 phải có sample
   riêng chốt trước và denominator rõ. Không trộn sample không ngang để nhận
   một so sánh paired hoàn chỉnh. Freeze vẫn yêu cầu đủ24checkpoints của plan.
5. Không thay human judgments bằng nhãn model/parser. Kiểm tra mù trên mẫu
   đại diện, giữ hai nhãn gốc, phân xử bất đồng logic và báo độ tin cậy.
6. Nhóm nguồn tự nhiên/ngoài có license và semantic audit phải báo riêng; không
   gọi template do AI/code tạo là truyện human-authored. Chưa có nhóm này được xác nhận.

Nếu chưa có người đọc/công sức phù hợp, manuscript có kết quả chưa thể hoàn tất.
Đây là một evidence gate; tăng GPU-giờ không giải quyết được nó.

## Rà soát analyzer trước dùng nhãn thật

Inspection phát hiện Q3-A đang dùng readerA cho coverage/fluency khi không có
adjudication; B/C đã có averaging hai reader. Cần giải quyết và regression-check
aggregation này **trước phân tích nhãn thật**. Primary logical success/adjudication
vẫn là protocol riêng. Chưa thay code training/evaluation trong immutable bundle
đang chờ Drive auth; mọi analysis revision phải có hash và provenance rõ, không
âm thầm làm checkpoint/plan cũ có vẻ do code mới tạo.

Các trường `smallest_useful_effect`, `gpu_hours_cap_per_study`,
`test_source_ids`, `naturalistic_transfer_manifest` còn trống theo đúng tình
trạng chưa có evidence. Không điền số/human labels để vượt gate hình thức.


## 2026-11-26 — Analysis correction verified

[Versioned analysis review](Q3_A_ANALYSIS_REVIEW.vi.md): average both readers for coverage/fluency; require complete source/seed/role/arm panels, original generation checks and prospective analysis/source registration.15new regression tests; full suite148passed/12deselected. Training bundle/plan unchanged. No real human labels, scientific outputs or cloud progress established; Drive handoff remains pending.
