# Q3-A: lượt7 đã audit, lượt8 đang chạy — 27/11/2026

Lượt7 session `20261126T184845Z`, T4, return0,1085,1849/1100giây soft cap.
Transformer **3.681.984tham số**:80.000.000LMtargets + **12.741.029/20.000.000
SFTtargets**, tổng92.741.029targets/101.149.631input tokens/170.401updates.
minGRU3.682.887tham số chưa train. Đây là hai baseline, không phải MIM.

Lượt7 thêm4.956.996response targets,8.227.872inputtokens,31.369updates;
975,490428465optimizer giây, khoảng5081,54targets/optimizer giây. Peak tensor
allocated238.502.912bytes là metric ghi bởi chunk, không tổng VRAM gồm allocator/
driver. Cumulative optimizer6171,943626982giây. LM-final80M và scalarPPL trước
SFT không đổi thành kết quả100M; chưa có PPL hoặc writing mới.

Archive đọc lại độc lập qua Drive connector:

- `20261126T184845Z-foundation-evidence.zip`,120.097.299bytes/78members.
- SHA256 `1dd45d2858b7c91dc67b6459e225862d715a1bf3e22fdaa850d729655eda1bf8`.
- Latest `abc8ec834bae6aa54a9067206104ff312a5704206300c18fba564f3dfffaf835`.
- Previous `bfc7b476cc756326f55812ee9936c06f55e041f6d4797ec23e16f88943cc2148`.
- LM-final `84ce54dc104013da04e98100b2654fa5bb122a24dcac275116b2a6751644b81c`.

Verifier kiểm170.401finite/contiguous metric rows, stages/counters, checkpoint
hash chain, ledger/annex, không load pickle hoặc optimizer. Lần đầu gọi verifier
đã chạy trước khi process tải file kết thúc và bị từ chối; chờ **cùng download
handle** hoàn tất mới kiểm lại. Không đổi expected digest hoặc tải đè để pass.

## Hai chẩn đoán cùng checkpoint, không optimizer

Cell32 tự chạy sau khi7terminal và ledger đủ7finished; copylatest kiểm hash ổn
định. Cả hai receipt đã được fetch lại độc lập, kiểm SHA rồi gọi local checker.

- FP32 diagnostic SHA
  `523d10df95fca9328088f2b8f10d5774cdcda7d6197567eb5e6b9f41fa4b5fe9`:
  fixed641/1024panel, argmax0,max top40L1=1,51410558696e-5; train loss/grad
  flagTrue/False bitwise bằng nhau. Đây là checkpoint khác với lượt6; không
  xóa FAIL cũ, không chuyển backend trở lạiFP32 theo kết quả từng checkpoint.
- Canonical CPU/FP64 SHA
  `bda4659150dcc3f89acce53f7921c3d96639f9bc056c437a878fa48a1ebc6420`:
  max logit path error8,52651282912e-14, max top40L1=5,11828670809e-14,
  argmax0, causality/reset0, weights/checkpoint unchanged. Đạt cùng giới hạn
  1e-10/1e-4/0 của policyca5621d4…; không thay scientific metric hoặc cap.

## Tiếp tục trong phạm vi đã cấp

Sau audit, lượt8 session **`20261126T191245Z`**, Cell33, đã được quan sátExecuting
và Drive ledger xác nhậnreserved1100s. Không gọireservedlàfinished. Child
receipt khóa đúnglatestabc8ec…/FP32proof523d10…/FP64proofbda465… và wrapper
602323635119c2222a281a140e3bd81c0d9f5cb8526415d50bdba0093af94524.
Cùng T4/Drive mount, không xin grant lại. UI590,25CU/rate1,87 khi bắt đầu8;
anchor597,61/dropcap16CU/max16drivers giữ nguyên, không muaCU. Số invoice
quy thuộc riêng workload chưa có.

Tại audit7,7.258.971SFTtargets còn lại của Transformer tương ứng khoảng1428,5
optimizer giây **nếu** tốc độ lượt7 giữ nguyên, chưa gồm setup/I/O/audit. Đây là
projection có điều kiện, không bảo đảm giờ hoàn tất. Throughput train minGRU
trên T4 hiện tại **chưa đo**; không dùng projectionTransformer cho model ấy.

Code và bộ34writing prompts đã chuẩn bịFP64 cùng prospective reading rule;
chưa sinh panel vì chưa đủ hai complete100Mparents. TransferFairytaleQA mới
auditmetadata, chưa có cặp đã duyệt.233defaulttests/18trainingdeselected là
kiểm code, không kết quả khoa học. Không primary post/test/humanlabels/LaTeX
hoặc drafted-with-results/submitted/accepted/published. Goal vẫn active.
