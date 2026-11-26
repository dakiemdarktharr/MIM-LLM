# Q3-A: audit lượt 11, đo SFT thật và tiếp tục lượt 12 — 27/11/2026

Session `20261126T203337Z` kết thúc return0 sau1084,1983/1100giây soft cap.
minGRU factorized ứng viên tuyến tính, **3.682.887tham số**, đã hoàn thành
**80.000.000LM targets** và **1.299.378/20.000.000SFT response targets**;
81.299.378targets,82.156.795inputtokens,97.974updates. Transformer
**3.681.984tham số** giữ nguyên parent100M; cả hai là baseline, không phải MIM.
Chỉ một trong sáu parent dự kiến đã hoàn tất, chưa có panel viết mới.

## Persistence và numerical review

ZIP301.394.499bytes được đọc lại độc lập qua3phần có hash, ghép đúng producer:
`f080f7b5bb6e5f3d8fb1cdd4dc66bca44b1ba39e73ef91df1bf9773802b2b9bc`.
Audit lúc2026-11-26T20:57:08Z kiểm **127members/314.340step rows** hữu hạn/liên
tục, stage/input/target counters, ledger/resource annex và checkpoint hashes;
không load pickle trong bước ZIP audit. Mount vẫn giữ, không gọi là sau release.

- minGRU latest: `ae1736a5b704a0fbc6c0ab9a4f22eca1e118f61c77ff0f9bec375f346657e7bf`.
- minGRU LM boundary: `8dce2ef3500d04eda569d35caa02068891b324b1ecce1265a8896bd6fcf14338`.
- Diagnostic index: `b9d26aaee6e5c6c45aa43f29c84d9f7b7710ce4586c90b76114f8d457d976859`.
- Parts manifest: `a232f617c712fb8ff1c86792b7066adf1fdb0490f1b7831933136d7705dd5c9a`.

Transformer proof chỉ tái dùng khi checkpoint/source/policy/receipt byte hash
không đổi; final/latest tensors/identity/stats được kiểm lại bằng nhau. minGRU
được kiểm mới trên fixed train1024/validation641 panel: FP64 max logit path
error4,0856207e-14, top40L1=1,0674648e-14, argmax khác0. Đọc lại riêng raw JSON
và `check_review` local đạt policyca5621d4…; loss/gradient FP32 khi đổi cờ MHA
bằng nhau bitwise. Không đổi bounds1e-10/1e-4/0 hoặc xóa failureFP32 cũ.
Đây là numerical evidence trên panel đã khai báo, không là điểm viết/logic.

Trainer ghi general-validation LM tại80M: CE2,448318228, PPL11,5688741 trên
61.573BPE targets. Đây là diagnosticFP32 cuối pha LM, không chấm chất lượng
viết hoặc kết quả SFT cuối. Kết quả âm retention của Transformer9,41→83,44
sau SFT được giữ ở audit9; chưa chọn parent khác hoặc đổi lịch theo kết quả.

## Thông lượng đã đo

Đoạn chuyển pha có cả LM và SFT nên không dùng riêng nó tính SFT throughput.
Đoạn cuối chỉ chạy SFT đã thêm **905.053response targets/5.730updates** trong
**78,497542optimizer giây**, wall88,0086giây: khoảng **11.529,70targets/optimizer
giây**. Peak allocated toàn lượt1.808.646.144bytes, khác tổng VRAM.

Còn18.700.622response targets ở mốc audit. Nếu giữ đúng tốc độ ngắn vừa đo,
phần optimizer còn khoảng27phút; chưa gồm I/O, validation, numerical review,
cloud readback và nguy cơ runtime hết khả dụng. Đây không phải dự báo thời gian
hoàn tất paper, không phải GPU-giờ hay hóa đơn CU cuối. Không dùng tốc độ LM
để thay SFT. Giữ cap16drivers/16CU observed-drop; không tự tăng nếu dự báo sai.

## Lượt 12 và các gate còn thiếu

Driver12 session **`20261126T205946Z`** đã live, ledger12reserved được đọc lại
qua connector. CùngT4/mount, quan sát trước launch586,97CU/rate1,87. Source
12.700bytes được kiểm AST/diff, upload Drive rồi đọc/hash trướcexec:
`1dc27dcad46e4a0f226662954eeb6135d4b40c4eb54eb9dbefa979bbf35c088c`.
Chỉ đổi index/checkpoint/receipt/CU đã quan sát; core plan c18, tokenizer,
data/optimizer/schedule/caps giữ nguyên. Host có read-only follow-up sau train,
không tự mở driver13. Không grant mới hoặc mua thêm.

Writing vẫn chờ cả hai parent100M và34phiếu tác giả thật theo rule đã chốt;
post/seed mở rộng, primary test, licensed transfer, người đọc thứ hai và bản
thảo có kết quả chưa hoàn tất. LaTeX chưa compile, không có milestone editorial.
Song song đã cập nhật bằng chứng J.UCS từ Clarivate/Scopus trực tiếp; JCR/funding
và chất lượng scientific vẫn chưa được chứng nhận bởi các chỉ mục đó.
