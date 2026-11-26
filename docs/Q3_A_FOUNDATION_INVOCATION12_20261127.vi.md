# Q3-A: audit lượt 12 và resume phần SFT còn lại — 27/11/2026

Session `20261126T205946Z` kết thúc với return code 0 sau **1.085,1657 giây**
trong soft cap 1.100 giây. minGRU ứng viên tuyến tính factorized,
**3.682.887 tham số**, đã học đủ 80 triệu LM targets và **12.248.567 / 20 triệu
SFT response targets**. Tổng 92.248.567 targets, 100.333.552 input tokens và
167.292 updates. Transformer **3.681.984 tham số** giữ nguyên parent 100 triệu
targets đã hoàn tất. Cả hai là baseline, không phải MIM.

## Bản lưu và kiểm tra số học

Ba phần archive được tải riêng qua connector Drive, kiểm hash từng phần rồi
ghép đúng ZIP gốc **296.656.536 bytes**. Audit độc lập lúc
`2026-11-26T21:23:41.194702Z` xác minh **137 members / 383.658 dòng step metric**,
các counter theo pha, ledger và checkpoint hashes. Kiểm archive không load
pickle; bước numerical review riêng dùng các proof đã kiểm hash và policy cũ.

| Bằng chứng | SHA256 |
|---|---|
| Archive | `b2471c51817b265732627f1c21691120b236e981ebc16a8a8592112b7db1482b` |
| Parts manifest | `f08b634ff87c9ce1882a0a9789383e6c48199e34949172a3692fa5fb96cf8e45` |
| minGRU latest | `7ed081a7dc113528089858aa1d1409566f84a3cdc7266a264147b78c3291c9ee` |
| Diagnostic index | `3a52505da36a403a8376ecd8c78f21f6970a08fd5b756184794499daf1ea74a0` |
| minGRU FP32 proof | `3644898c1ba3f3bc0e3195b9806aa4d47d667371049e989f2f98558ebff6e274` |
| minGRU FP64 proof | `9cd311615952deeabc1fa95f0e2a67e7199b52373c927150866cd7befe99d204` |

minGRU FP64 max path-logit error **5,86198e-14**, max top-40 distribution L1
**1,32551e-14**, argmax khác **0**. Đọc lại proof qua connector rồi chạy
`check_review` local đạt policy không đổi. Loss và gradient FP32 dưới hai cờ
MHA vẫn bằng nhau bitwise. Transformer chỉ tái dùng proof sau khi đối chiếu
checkpoint/source/policy hashes không đổi; tensors/identity/stats final và
latest được kiểm lại bằng nhau. Không tuyên bố chạy một diagnostic mới cho
weights cũ. Các failure FP32 lịch sử vẫn giữ nguyên.

Mount được giữ, không có grant mới. Audit này không được gọi là đọc lại sau
khi release VM. Weights, raw metric và source story chỉ giữ local/Drive;
GitHub chứa tóm tắt và hashes. JSON tổng hợp phân biệt status do producer ghi
trước audit với kết luận independent review đã thực sự xảy ra.

## Thông lượng đo trên cả lượt SFT

Cả 9 chunk đều chỉ học SFT: **10.949.189 response targets / 69.318 updates**
trong **929,786206 optimizer giây**, tương đương **11.776,03 targets/giây**.
Wall driver 1.085,1657 giây bao gồm I/O và export, chưa bao gồm numerical
follow-up hoặc cloud readback. Peak allocated cao nhất 265.084.928 bytes,
không phải tổng VRAM hoặc memory footprint của toàn runtime.

Còn **7.751.433 SFT targets** ở mốc audit. Dự báo có điều kiện theo tốc độ
vừa đo là **658,24 optimizer giây / 10,97 phút**; chưa gồm I/O, validation,
numerical review, readback và runtime availability. Không thay bằng thời gian
hoàn tất paper hay hóa đơn CU thực tế.

## Lượt 13 và phần chưa hoàn tất

Driver 13 session **`20261126T212456Z`** đã chạy ở Cell 42 và ledger reservation
được đọc lại qua connector. UI trước launch: **586,20 CU, khoảng 1,87 CU/giờ**.
Giữ cap 16 drivers / 16 CU observed balance drop, cùng T4/mount, c18 plan,
data, tokenizer, optimizer và lịch học. Source host 12.699 bytes đã kiểm AST
và diff, lưu Drive rồi đọc/hash trước exec:
`e6b33e8eacc98a0d70c132f42feeb465f5a777694bcdaa170ee3d98f305d6e38`.
Không tự mở driver 14 hoặc mua CU.

Writing feasibility vẫn chờ cả hai parent 100 triệu targets, đủ 34 mẫu và
nhãn tác giả thật theo rule chốt trước. Hướng dẫn tiếng Việt cũng được ghi
trước khi sinh mẫu. Chưa có post-training chính, test, transfer hợp lệ hoặc
đánh giá người đọc độc lập. Kết quả âm general-validation retention của
Transformer vẫn giữ; không chọn lại checkpoint để tránh kết quả đó.
Manuscript có kết quả và LaTeX còn bị gate; chưa có submission/acceptance.

Receipt: [`foundation_invocation12_results.json`](../configs/q3a/foundation_invocation12_results.json).
