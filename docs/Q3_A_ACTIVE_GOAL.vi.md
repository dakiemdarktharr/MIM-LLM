# Goal Q3-A — active từ 26/11/2026

> **Trạng thái hiện hành, 26/11/2026:** goal ACTIVE; Drive đã giải quyết.
> Calibration2 hoàn tất cả hai baseline 50M target/model sau 3/3 lượt; GPU đã
> trả lại. Archive 53 tệp/81.262 dòng metric đã tải lại và kiểm tra độc lập.
> Writing gate vẫn chưa đạt sau khi đọc đủ 34 output: không mở A0–A3, test,
> thêm lượt calibration2 hoặc biên dịch LaTeX. [Báo cáo đo thật và chẩn đoán](Q3_A_CALIBRATION2_RESULTS_20261126.vi.md).
> Các đoạn `blocked` phía dưới là lịch sử đã được thay thế. Hiện chỉ có người
> dùng làm reader; chưa có nhãn người hay độ đồng thuận giữa hai reader.

Người dùng yêu cầu tiếp tục tới khi train, viết, đối chiếu tài liệu và kiểm tra
chất lượng bài hoàn tất. Đây là Q3-A đang triển khai; B/C/Q1 chưa được cấp lệnh
train. Goal không phải cam kết acceptance hoặc quartile của một bài tương lai.

## Điều kiện hoàn thành có thể kiểm chứng

1. Scope và incremental novelty đối chiếu primary literature; đóng góp độc lập
   rõ ràng, giữ stop/merge conditions khi không đủ giá trị khoa học.
2. Training đúng plan/run/seed, input/token/compute controls, trong CU hiện có và
   resource caps đã đo/chốt. Kiểm tra writing feasibility trước full matrix;
   không tự mua thêm credits hoặc đổi benchmark để săn kết quả thuận chiều.
3. Drive có checkpoint/previous, optimizer/RNG/cursor, nguồn/config/code/data
   hashes và metric logs được xác minh đọc lại. Công khai replay/lỗi/chi phí.
4. Validation selection và analysis/source/resource registration khóa trước test.
   Báo từng seed, source-paired uncertainty, mandatory coverage, contradictions,
   fluency/PPL và failure cases. Human judgments phải do người thật cung cấp.
5. Bản thảo tiếng Anh dùng kết quả thật, prior-work comparison, limitations,
   negative results và reuse disclosure; LaTeX compile và PDF visual QA đạt.
6. Audit reproducibility/statistics/claims và yêu cầu journal Q3 xác minh đúng
   ngành/năm/phí; không mặc định acceptance, funding hoặc Q3CS từ Q3Linguistics.
7. Obsidian và public development log cập nhật, code/docs commit/push; PDF,
   checkpoints/rawdata/private notes giữ local/Drive. Không tự nộp bài.

Nếu một scientific gate thất bại, ghi bằng chứng và sửa scope hoặc đề xuất
gộp/dừng; không đánh dấu goal complete chỉ vì đã chạy hết ngân sách. Các mốc
drafted-with-results, submitted, accepted và published theo dõi riêng.

## Trạng thái khi tạo goal

Đã xác minh Pro+ đúng tài khoản theo yêu cầu. Đã tạo notebook nhẹ trên Drive:
the private Q3-A training notebook (URL retained in local/vault receipts).
CPU runtime đã kết nối, source-bundle.zip đã upload. Colab đang yêu cầu người
dùng cấp quyền notebook truy cập Drive; **chưa có cloud warm-up/metric/checkpoint
được xác minh**. Goal vẫn active, chờ bước quyền truy cập ngoài khả năng tự cấp.

Plan `ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142`;
bundle SHA256 `2ad7e8d63189ffc84b5802cf31df01950d596bc2d57021a56f8f9e7240ac6f2b`.
[Scope review](SCOPE_REVIEW_BEFORE_TRAIN_20261126.vi.md) đã thay A2 bằng numeric
nuisance-clock control trước train. 133 non-training tests và4 authorized
optimizer/overfit/resume tests đạt; không coi unit fixtures là scientific results.
Initial GPU invocation cap20phút phục vụ calibration/feasibility; không phải
điều kiện tự kết thúc goal. Các lượt tiếp theo phải dùng checkpoint/cost đã đo.


## 26/11 — Evidence audit update

[Journal verification](Q3_A_JOURNAL_VERIFICATION_20261126.vi.md), [annotation feasibility](Q3_A_ANNOTATION_FEASIBILITY.vi.md) and `configs/q3a/evidence_gates.json` identify what is verified and still missing. No browser poll while manual Drive handoff is pending; no cloud progress assumed.


## 2026-11-26 — Analysis correction verified

[Versioned analysis review](Q3_A_ANALYSIS_REVIEW.vi.md): average both readers for coverage/fluency; require complete source/seed/role/arm panels, original generation checks and prospective analysis/source registration.15new regression tests; full suite148passed/12deselected. Training bundle/plan unchanged. No real human labels, scientific outputs or cloud progress established; Drive handoff remains pending.


## 26/11 — Superseding phase order

User explicitly requires actual data collection, training, test/evaluation and result analysis before any further LaTeX compilation. Both build scripts now stop before compiler access without real phase evidence. No TeX was run after this instruction. See [phase order](MANUSCRIPT_PHASE_ORDER.vi.md). Historical layout receipts do not release this hold. Goal still requires actual experiments and manuscript, and manual Drive consent remains pending.


## 26/11 — Trạng thái mới nhất: blocked, chưa hoàn thành

Goal tool đã xác nhận `blocked`: chờ người dùng hoàn tất quyền Drive và trả quyền điều khiển trình duyệt. Điều kiện này lặp qua ít nhất ba goal turns; các phần chuẩn bị độc lập đã được thực hiện trước khi chuyển trạng thái. Không có job train từ xa đang chạy được xác minh. Không poll browser khi takeover còn pending. Toàn bộ mục tiêu và quyền train Q3-A vẫn giữ nguyên; không xin lại quyền train. Sau khi được trả điều khiển, xác minh Drive mount/persistence rồi tiếp tục warm-up giới hạn và các pha thí nghiệm. Không compile thêm trước kết quả thật.
