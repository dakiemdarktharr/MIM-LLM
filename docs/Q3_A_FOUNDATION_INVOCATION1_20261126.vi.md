# Q3-A — lượt đo foundation đầu tiên, 26/11/2026

Lượt đo kết thúc, **nền ngôn ngữ chưa hoàn tất**. Goal toàn bài vẫn active;
không có kết quả A1−A2, writing gate mới, human labels hoặc final-test performance.

Plan `c18fcecd62ada83af8de97752496dac7b89837197206b5d7398bd81f4b4eca41`,
run `foundation-transformer-s0`, scientific learning/data unchanged.

| Nội dung | Giá trị thực |
|---|---:|
| Transformer parameters | 3.681.984 |
| Token targets LM đã học | 6.559.500 / 80.000.000 |
| SFT targets đã học | 0 / 20.000.000 |
| Optimizer updates | 7.366 |
| Input positions đã xử lý | 6.559.500 |
| Cumulative optimizer-training seconds | 296,567835511 |
| Driver elapsed / reserved soft cap | 342,990531405 / 360 s |
| Target/s theo training seconds này | 22.118,0425 |
| Peak CUDA allocated memory lớn nhất trong 3 chunks | 2.135.539.712 bytes |
| minGRU foundation | Chưa bắt đầu; cấu hình thực 3.682.887 params |

NVIDIA L4, PyTorch2.14.1+cu130, float32/TF32 disabled. Thông lượng trên đây gồm
forward/backward/AdamW/clipping/synchronize của các cập nhật; loại batching,
log/checkpoint/Drive/setup/validation nên không phải wall-clock cost toàn bộ.
Không dùng số này làm thông lượng SFT hoặc minGRU chưa đo.

Train token-weighted CE trên100updates đầu/cuối:10,38106568 /2,87697987.
Đó là các batch khác nhau khi đang train, **không** là held-out PPL, kết quả
viết, hiệu ứng phương pháp hay chứng minh generalization.

## Kiểm chứng

Trước updates,8CUDAcases:2backbones×length32/128/512/1024; dense train path,
dense eval,cached chunk,step-by-step cached forward khớp với maxabs1,6391277e-5
(tolerance2e-4), future edits/past logits error0. Đây là random-init path checks,
chưa phải kiểm lại checkpoint đã train của foundation.

Checkpoint latest SHA:
`9534ba29f99ee7d67b51e1265400bd14bc3ea63527aa40142cf20feed9b7df12`.
Remote previous SHA bằng latest của chunk ngay trước:
`8818878184b291d409766315e1938b99d475d51c8da72c79b49469e01fafa6ae`.

Cloud evidence ZIP82.309.391bytes, SHA
`7bcf7c471ed90559cc1865d56072312c2292756936448ec69b0068d0bdeff243`.
Hash gốc lấy từ console persisted riêng; archive được tải qua Drive connector
sau khi UI0sessions được đọc. Verifier không load pickle, kiểm16member hashes,
7366updates liên tục, exact stage/total/input accounting, finite CE/gradient/LR/
time và matching checkpoint/event. Tệp private giữ ở
`artifacts/q3a-foundation-20261126`; report public machine-readable:
`configs/q3a/foundation_invocation1_results.json`.

## Lỗi vận hành và tài nguyên

Phiên setup-only riêng trước đó:0optimizer, bundle92.702.119bytes/73payloads
đã kiểm cả DriveFS lẫn độc lập cloud readback sau release. Giữ v1ZIP và v2
overlay. Hai mount timeout của VM train được khôi phục; cap driver rút từ
900s dự kiến xuống360s, vẫn chiếm1/8slot; không cấp thêm slot bù thời gian.

Sau export, child gọi Colab `runtime.unassign()` rồi lỗi callback thiếu IPython
kernel; không xem là lỗi loss/checkpoint. UI sau đó cho0active sessions/rate0,
596,66CU. Mã chính chủ hiện hành yêu cầu backend unassign trước JS disconnect
callback; đây là căn cứ giải thích có thể xảy ra, không phải snapshot package
đã cài. V3 chuyển release về notebook host sau flush/unmount, tránh child return
code lỗi ở bước UI. [Nguồn Colab](https://github.com/googlecolab/colabtools/blob/main/google/colab/runtime.py)
(tra26/11/2026).

Balance quan sát trước setup597,61, trước driver597,05, sau release596,66CU.
Các hiệu balance chưa là hóa đơn riêng của job. Account Pro+ và L4 rate2,33CU/h
đã đọc UI; High-RAM bắt buộc theo lựa chọn L4. Không mua thêm tài nguyên.
Browser control từng mất do app không còn mở; khôi phục đúng app/notebook và
theo dõi qua Drive trong khoảng đó, không restart trùng job.

## Quyết định kế tiếp

Chỉ phần Transformer LM còn lại ước tính3320,39s **optimizer training** nếu giữ
thông lượng quan sát. minGRU/SFT chưa đo,7driver còn tối đa7700s. Chưa chứng minh
toàn bộ100Mtargets/model có thể hoàn tất trong cap. Trước optimizer tiếp theo:
đo train-only forward/backward không cập nhật cho cả4model×stage combinations,
ghi phần chưa bao gồm/uncertainty và quyết định resource feasibility. Không
gán đầu ra profiler là scientific result hoặc âm thầm hạ target để gọi complete.

Chỉ user có thể đọc đánh giá hiện tại,0nhãn thật. Postmatrix/seeds khác/B/C/Q1,
tokenizer fitting, test và LaTeX vẫn chưa mở. Không có thành tựu biên tập mới.
