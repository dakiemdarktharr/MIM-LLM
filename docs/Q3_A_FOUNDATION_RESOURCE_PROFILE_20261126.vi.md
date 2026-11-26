# Đo tài nguyên và đề xuất điều chỉnh thời gian — 26/11/2026

## Số đo thực

L4, PyTorch2.14.1+cu130, FP32/TF32off, batch4, seed0, đúng c18plan. Mỗi
kind/stage lấy32trainbatches đầu theo thứ tự đã khai báo, thêm2nonupdatingwarmups.
Không optimizer, không đổi learned weights, không dùng validation/test.

| Backbone | Stage | Targets đo | Forward/backward s | Target/s | Peak allocated bytes |
|---|---|---:|---:|---:|---:|
| Transformer | LM | 30.950 | 0,921909 | 33.571,66 | 1.618.710.016 |
| Transformer | SFT | 5.198 | 0,697586 | 7.451,41 | 181.584.896 |
| minGRU variant | LM | 30.950 | 0,681241 | 45.431,77 | 1.264.253.440 |
| minGRU variant | SFT | 5.198 | 0,366348 | 14.188,70 | 181.571.584 |

Tham số thực giữ3.681.984/3.682.887; đây là hai baseline khôngMIM. Mỗi learned
parameter được kiểm bitwise bất biến sau profile, gradients finite. Chỉ đo
khoảng32batch ở random initialization: **không** phải full-training throughput,
không ước lượng bất định của cả corpus hay bằng chứng chất lượng.

Nhân số targets chưa học với chi phí forward/backward mẫu cho tổng8042,083s
(134,03phút), trong khi7driver còn lại chỉ tối đa7700s(128,33phút). Đây là
ước tính lạc quan compute-only, không phải một cận dưới toán học đã chứng minh
cho mọi batch. Còn thiếu AdamW, host/log, đánh giá, lưu checkpoint/Drive/setup;
vì vậy feasibility trong trần cũ **không đạt điều kiện đã đặt ra**. Không gọi
hai foundation complete, không tự giảm100Mtargets/model hoặc chạy driver2.

Profile SHA`05dbe95887aa98d1d6f24f4a5f2f90ec24a2891049799f524ab604ca11a49b17`;
assessment SHA`34642b184653d6d5372565e221228587cf801cac824971b5b228aef47749e343`.
Cả hai JSON được tải lại độc lập bằng Drive connector và khớp SHA notebook.
Ledger không đổi trong profile, vẫn1/8driver. UI596,66CU/rate2,33CUh là quan
sát, chưa có hóa đơn quy thuộc. Drive/VM giữ mount khi profiler thành công
theo yêu cầu mới; không giữGPUidle vô thời hạn khi chưa có bước hợp lệ tiếp.

## Điều chỉnh tài nguyên có hiệu lực trước driver2

`configs/q3a/foundation_resource_annex.json` nâng tổng số
driver tối đa8→16, vẫn<=1100s/driver, còn tối đa16500s(4giờ35phút) driver.
Giữ trần observedCUdrop16 tính từ UI597,61, không mua CU/subscription, không
đổi architecture/tokenizer/data/targets/seed hoặc decoding. Giữ checkpoint
hiện có để resume đúng learning plan; annex tài nguyên phải có hash/provenance
và verifier/ledger kiểm riêng, không sửa học trạng thái cũ thành plan mới.

Ở rate quan sát2,33CUh,4giờ35phút driver tương ứng khoảng10,68CU **theo phép
nhân giả định rate cố định**, chưa gồm setup/đồng bộ/idle và không là dự báo
đã đo toàn workload. Trần16CU vẫn có quyền dừng trước hoàn tất; nếu rate thay
đổi hoặc tốc độ thấp hơn thì báo incomplete. Không mở grid/seed/A0–A3/B/C/Q1
hoặc test bằng annex này. Không hứa đủ ngân sách hay kết quả viết tốt.

Trần8driver là giả định lập kế hoạch của agent, không phải yêu cầu người dùng
dừng sau8lượt. Quyền hiện có yêu cầu hoàn thànhQ3-A trong CU đã mua. Vì vậy
annex này là quyết định triển khai trong phạm vi đã cấp, không xin lại quyền
Drive hoặc mua thêm. Sửa rõ điều khoản8lượt của protocol cũ bằng annex có hash,
có hiệu lực trước driver2, giữ trần16CU và không thêm exposure khoa học ngoài
80MLM+20MSFT/model đã khai báo. Không sửa hồi tố ledger/receipt lượt1.
Goal toàn Q3-A còn active, chưa compileLaTeX.
