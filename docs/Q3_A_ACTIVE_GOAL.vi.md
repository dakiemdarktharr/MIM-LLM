# Goal Q3-A — active từ 26/11/2026

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
