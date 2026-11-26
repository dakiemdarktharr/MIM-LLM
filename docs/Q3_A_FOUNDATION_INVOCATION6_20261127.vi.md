# Q3-A: audit lượt6 và sửa backend suy luận — 27/11/2026

## Kết quả train thực

Session `20261126T181247Z`, T4, return0; 1084,9566/1100giây soft cap.
Transformer **3.681.984 tham số** hoàn tất80.000.000 LM targets, đang ở
**7.784.033/20.000.000 SFT targets**, tổng87.784.033targets/139.032updates.
minGRU3.682.887tham số chưa bắt đầu; cả hai không phải MIM. Lượt này thêm
4.998.197SFTlabels trong978,2063optimizer giây, khoảng5109,55labels/giây;
input8.293.337tokens khác số nhãn. Đó không phải thông lượng gồm I/O/audit.

Archive119.951.876bytes,63members đã tải qua connector riêng và audit đầy đủ
139.032dòng metric hữu hạn, liên tục, stage/counter/annex/hash; không load pickle.

- Archive SHA256 `82f219033d23397381ff6658e1d2f955b04daaa71904f852ca9857839c1f3fec`.
- Latest `34fbfa701c1eb9e5053b866c6e250c592869275511cdaea7ec16edda77656520`.
- LM-final `84ce54dc104013da04e98100b2654fa5bb122a24dcac275116b2a6751644b81c`.
- Previous `f73165f0a439e999cc67d8c7b675b05d85ad746d467f23436dc925cf7fc57f97`.

Cumulative optimizer5196,4532giây; GPU UI591,18CU/rate1,87 ở lần đọc sau chẩn
đoán, không phải invoice riêng cho train. 6/16driver slots đã dùng; cap16CU
theo anchor597,61 vẫn giữ. Drive giữ cùng mount; không xin cấp quyền lại.

## Gate FP32 thất bại, giữ nguyên kết quả và giới hạn

Receipt `800791f42be1160960188e6d79ced5ec9c725472427d4fe7d242f1711d666883`
đã đọc lại độc lập và local checker xác nhận **FAIL** theo policy4ee4ddd2…:
max top-40 probability L1 `0.0057072127768849346` vượt `0.0001`.
Full-vocabulary L1 chỉ1,22358e-5, argmax không đổi. Không đồng nhất các chỉ số
này: top-k cắt bỏ token tạo phép biến đổi gián đoạn tại biên hạng k/k+1.

Chẩn đoán biên riêng SHA
`5075d7562ccd62b28ba6a29ee6b46b8645ab657bbd395cd4e3ed5e26fa6aaa1c`
phát hiện1/1765vị trí validation641: batch1,time185 (index zero-based), token13
và2342 đổi vị trí40/41; marginFP32 khoảng6,68e-6 vàFP64 khoảng4,64e-6, logit
error tại vị trí9,05e-6. Phép tính policy trực tiếp trên GPU vẫn lệch0,00570756;
không chỉ là việc chuyển tensor sang CPU trong diagnostic cũ. Test train1024
không có event vượt giới hạn. Đây là bằng chứng phạm vi cố định, không là tỷ
lệ lỗi toàn corpus hoặc chất lượng viết. Không có optimizer trong chẩn đoán.

PyTorch2.14 mô tả [khác biệt số học giữa cách tính](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html)
và [thứ tự chỉ số khi top-k hòa điểm](https://docs.pytorch.org/docs/2.14/generated/torch.topk.html).
Trường hợp đo được là hai điểm rất gần nhau, không phải khẳng định chúng hòa
điểm chính xác. Tài liệu chung không tự chứng minh nguyên nhân của từng run.

## Bản sửa đã kiểm tra: CPU/FP64 cho suy luận

Không tăng ngưỡng cũ. Thêm backend riêng
`CPU_FP64_MHA_off_stable_token_ID_topk_v1`: promote bản copy của weights FP32
sangFP64, tính cả forward và samplingFP64 trênCPU, exact ties theo tokenID tăng.
Đặt cùng backend cho cả hai backbone và mọi arm trước khi có primary outputs.
Tokenizer, prompt, max128BPE, temperature0,8, k40, seed17 không đổi; chuỗi seed
trênCPU có thể khác đề xuất samplingGPU/FP32 trước đây. Không được gọi hai
implementation là bitwise tương đương. Chi phí suy luận FP64 cần đo riêng.

Receipt FP64 `102f266836370b1b77551ee47cee6904af33f54759db2e5f244f378070172e7b`
đã tải độc lập/kiểm hash/checker: toàn641/1024panel,4paths, argmax mismatch0,
max logit path error1,66978e-13 trong tolerance1e-10, causality/reset exact0,
max top40L1=2,71120e-14 trong cùng bound1e-4. Weights/checkpoint không đổi;
FP32 train loss/gradient flagTrue/False vẫn bitwise bằng nhau, không optimizer.

Policy thay backend, có hiệu lực trước lượt7:
`ca5621d4d52d349ec22b7eabc4e35bf38984f9461016e7196f6e3c037d69ef48`.
Đây là sửa kỹ thuật sau chẩn đoán, công khai là posthoc; không preregistered
scientific finding, không sửa receipt FP32 thành pass. Launcher mới chỉ gọi
V4 trainer cũ sau khi khớp cả proof chain/checkpoint/source/hash/ledger.
Learning plan c18, trainingFP32, mục tiêu, dữ liệu, optimizer, quyền và cap giữ
nguyên. Mỗi checkpoint kế tiếp vẫn phải được kiểm lại; không bảo đảm toàn bộ
chuỗi sinh hoặc mọi checkpoint chỉ từ panel hiện tại.

Code PPL/general test và generation/analysis được ràng buộc backend mới;
foundation writing manifest phải tạo lại cùng17prompts do source hash đổi.
232default tests pass/18trainingdeselected, Ruff pass; test cố ý phá backend,
precision, threshold và text đều từ chối đúng. Các fixture là giả lập, không
nhãn người hoặc kết quả khoa học. C18 còn load đúng hash sau sửa.

Chưa có complete100Mparent, writing panel thật, primary post run, human label,
test result, LaTeX build hoặc mốc công bố. Goal vẫn active và chưa hoàn thành.
