# Q3-A: audit lượt8 và tiếp tục lượt9 — 27/11/2026

Session8 `20261126T191245Z`, T4, return0,1085,6251/1100giây soft cap.
Transformer **3.681.984tham số** đã học80.000.000LM + **17.658.120/20.000.000
SFTtargets**, tổng97.658.120targets/109.306.959inputtokens/201.513updates.
minGRU3.682.887tham số chưa bắt đầu tại mốc audit8; cả hai là baseline, không MIM.

Lượt8 thêm4.917.091response labels,8.157.328inputtokens,31.112updates;
972,217264214optimizer giây, khoảng5057,61labels/optimizer giây. Cumulative
optimizer7144,160891196giây. Peak tensor allocated236.480.512bytes không phải
tổng VRAM gồm driver/cache. Chưa có PPL mới hay output viết của foundation100M.

## Bản lưu đọc lại độc lập

- Archive121.549.983bytes/86members, SHA256
  `fe40343f8da67cac767f8c17f29f7b2564e962e155d9915eb40ada14ddcb2536`.
- Latest `050774cf8613ce8e880eb61f84737a4ddbf463743ed81be07a59b44516c4f2d9`.
- Previous `6c241dcc8c19b76ce323d6aff657f837fa90076c2f596f79247a9aff46522342`.
- LM-final `84ce54dc104013da04e98100b2654fa5bb122a24dcac275116b2a6751644b81c`.

Drive connector cung cấp raw ZIP; chờ download hoàn tất, kiểmsize/SHA trước
verifier. Audit đủ201.513metric rows hữu hạn/liên tục, stage/label/input counters,
ledger/resource annex và checkpoint hashes; không load pickle hoặc optimizer.
Đây là cloud readback khi VM còn mounted, không phải sau deallocation.

Cell34 chỉ chạy sau khi8terminal và ledger8finished; các receipt đã đọc lại và
kiểm hash riêng, rồi gọi local `check_review` với cùng checkpoint/source chain:

- FP32diagnostic `9019ee82ade2e495460ad75a65b2fef3ce1097c24f3b9c68f2204b9bbbf0441a`;
  max top40L1=8,88694970473e-6, train loss/gradient flagTrue/False bitwise bằng.
- CPU/FP64diagnostic
  `6b5eeea3636144c2b4a11d3f0b184274c3bdf6cbe305e0276c3efde2c7b69715`;
  max logitpatherror9,23705556488e-14, top40L1=3,42534160758e-14,
  argmaxmismatch0, causality/reset0, unchangedweights/checkpoint.

Đạt policyca5621d4… cùng bounds1e-10/1e-4/0; không đổi ngưỡng, scientificmetric,
optimizer hay backend theo dấu kết quả. FP32failure lịch sử vẫn giữfailed.
Không có optimizer hoặc test trong chẩn đoán. Số liệu máy chưa là điểm viết/logic.

## Lượt9 live và công việc sau nó

Cell35 bắt đầu session **`20261126T193700Z`**,1100ssoftcap; quan sátExecuting,
child receipt và Drive ledger đọc lại xác nhậnindex9reserved,8entriestrước
finished. CùngT4/Drive mount, không grant mới. UI589,63CU/rate1,87 lúc bắt đầu;
16drivers/dropcap16CUtheoanchor597,61 giữ nguyên, không muaCU. Actual invoice
quy thuộc chưa có. Basecontroller tiếp tục Transformer và có thể tạo/train
minGRU trong phần wall budget còn lại; không khẳng định xảy ra trước receipt.

Checkpoint live đầu của9 lúc19:39:08Z ghiSFT18.233.615/205.157updates,
latest `b01aa7194bdba68b2908b3255deaeccf0e87e0373162ef13f2a0c7b3fd3949af`.
Đó không phải archive cuối được audit. Các thống kê verified chính ở trên vẫn
thuộc8 cho đến khi9terminal và cloudreadback xong.

Cell36 được xếp sau9: guardledger9finished/childreturn0/pinned3sourcehashes,
copylatest ổn định của từng run có thật, kiểmidentity/updates. Run chưa bắt
đầu hoặc chỉ có0updates được ghi rõ không có numericalpass. Với từng run đã
học, tạo cả FP32diagnostic và CPU/FP64diagnostic (420stimeout/mỗi helper),
hashes/logs/indexlưuDrive. Không chỉ kiểm Transformer nếu minGRU đã học;
không tự mở driver tiếp theo. Final vàlatestcó thể khácfilehash: review viết
vẫn phải dùng đúng completeparent/final và evidence phù hợp khi đủ hai model.

Nguồn phương pháp tiếngAnh đã đồng bộsubword, giữ confirmation có điều kiện
và thiếu hụt hiện tại; kiểmstaticđạt, compiler vẫnkhóa.233defaulttests là kiểm
code. Chưa completeparentđủ2model, writing/human/post/primarytest/LaTeX hoặc mốc
công bố. Goalactive, giữ đầy đủ phạm vi Q3-A.
