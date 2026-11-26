# Q3-A: audit lượt 9 và chẩn đoán giữ năng lực ngôn ngữ — 27/11/2026

Lượt 9, session `20261126T193700Z`, đã kết thúc với return0 sau
1082,9848/1100 giây soft cap. Cùng T4 và mount Drive; không cấp quyền lại.
Giữ nguyên plan c18, tokenizer, dữ liệu, optimizer, lịch học và test khóa.

| Backbone | Tham số thực | LM targets đã audit | SFT response targets đã audit | Updates | Hoàn thành parent100M |
|---|---:|---:|---:|---:|---|
| Transformer của dự án | 3.681.984 | 80.000.000 | 20.000.000 | 216.366 | Có |
| minGRU ứng viên tuyến tính, factorized | 3.682.887 | 17.353.105 | 0 | 19.498 | Chưa |

Cả hai là baseline, không phải MIM. Đây là một trong sáu parent dự kiến, không
phải sáu seed đã hoàn tất hoặc một model trò chuyện đã được kiểm chứng.
Lượt9 thêm 2.341.880 SFT labels cho Transformer trong460,4876 optimizer giây,
khoảng5085,65 labels/giây; minGRU học17.353.105 LM targets trong503,5739 optimizer
giây, khoảng34.459,90 targets/giây. Hai tốc độ thuộc hai nhiệm vụ khác nhau,
không là so sánh chi phí trực tiếp. Peak allocated toàn lượt1.721.988.096bytes;
đó không phải toàn bộ VRAM. Chưa có hóa đơn CU quy thuộc chính xác từng run.

## Bản lưu độc lập

ZIP gốc275.033.915bytes vượt giới hạn một file của connector268.435.456bytes;
lần tải trực tiếp bị từ chối trước khi tải. Giữ nguyên ZIP, tạo3phần100MiB,
100MiB và65.318.715bytes. Đọc từng phần qua connector, chờ download hoàn tất,
kiểm SHA riêng rồi ghép lại. Size/SHA của ZIP ghép khớp đúng producer:

`b92fa27369389e92ad94494e958f025384982169495c2c35ce57f99a6f6d28d7`.

Manifest phần có SHA
`c0cdac19d81fb3ef38506ea4658663f4f0848bed9514df2fa812692a10e34017`.
Verifier kiểm100members và235.864step rows hữu hạn/liên tục, stage/input/label
counters, ledger và resource annex, lúc2026-11-26T20:04:23Z. Không load pickle
trong bước audit ZIP; mount vẫn hoạt động, không gọi đây là kiểm sau release.

| File | SHA256 |
|---|---|
| Transformer latest | `8d8a5a20de709b59fa2b1508e383dd582c0f9adf03cef61884e37573e0577beb` |
| Transformer final | `30c5b6b8a8006f4ce1bc4a7d962adcbe0548b13eeb395daca1b8694647964c45` |
| Transformer LM boundary | `84ce54dc104013da04e98100b2654fa5bb122a24dcac275116b2a6751644b81c` |
| minGRU latest | `05f8ad49d9667bdcc35b18c857e4189af52fd020dfeb591615eadd8b31062cb0` |

Đọc `weights_only=True` trên các file đã kiểm hash xác nhận toàn bộ model
tensors/identity/stats của Transformer final và latest bằng nhau tuyệt đối;
hai byte hash khác nhau do biểu diễn file. Cấu hình/tokenizer ràng buộc bởi
plan_id đã kiểm, không phải hai trường top-level không tồn tại. State dict
đếm alias embedding/head hai lần (6.898.432elements); số tham số học thực vẫn
là3.681.984, không dùng số elements ấy làm parameter count.

## Kiểm định số học của cả hai backbone

Cell36 tạo hai receipt/run, index
`7f0996ec6b7d6131449d0d378a6a0bf13d03ed3ff0b1f5feb5db3766250c6a57`.
Đã đọc lại từng JSON, kiểm hash độc lập và gọi local `check_review` với đúng
checkpoint/source chain. Cả hai đạt policy ca5621d4… đã chốt trước lượt7:

| Backbone | FP64 max logit path error | FP64 max top40 probability L1 | Argmax khác |
|---|---:|---:|---:|
| Transformer | 9,9475983e-14 | 1,8662643e-14 | 0 |
| minGRU | 3,9079850e-14 | 8,1742203e-15 | 0 |

Loss/gradient FP32 khi đổi cờ MHA bằng nhau bitwise; kiểm future edit/reset
đạt. Các kiểm tra dùng fixed validation/train panel, không test hoặc optimizer.
Không đổi bounds1e-10/1e-4/0; FP32 failure lịch sử vẫn là failure. Raw receipt
hashes đầy đủ trong `configs/q3a/foundation_invocation9_results.json`.

## Lỗi bộ đọc checkpoint đã sửa, kết quả âm đã giữ

Lần tính PPL đầu từ checkpoint thật bị từ chối vì bộ đánh giá đòi `config` và
`tokenizer_spec` top-level của **post** checkpoint. Checkpoint **foundation**
thực chỉ có identity/model/optimizer/stats/RNG/complete; fixture trước đó dùng
nhầm schema post và đã che lỗi này. Ad-hoc comparator cũng gặp `KeyError` cùng
nguyên nhân. Không tạo metric thành công, không thay checkpoint hoặc optimizer.
Giữ failure receipt cục bộ. Đã sửa reader: foundation dùng verified plan_id và
strict model load; post vẫn kiểm explicit metadata.15tests liên quan đạt và
Ruff đạt. Cell kiểm định xếp sau train được thay trước khi thực thi; train10
không bị ngắt. Không sửa source thuộc fingerprint foundation c18.

Replay read-only trên **cùng300validation stories/61.573BPE targets, gồm EOS**,
CPU/FP64, toàn vocab không temperature/top-k, đo ở Windows máy thật:

| Checkpoint | NLL nats/target | Perplexity | CI95 theo truyện nguồn |
|---|---:|---:|---|
| Sau80M LM, trước SFT | 2,241714569 | 9,4094506 | [8,9853;9,8400] |
| Sau80M LM+20M SFT | 4,424111775 | 83,4386620 | [72,9950;95,3006] |

Perplexity là exp(NLL trung bình), thấp hơn tốt hơn khi cùng tokenizer và tập
đánh giá; không phải xác suất viết đúng hoặc điểm fluency. Chênh NLL sau−trước
là **+2,1823972**, paired-source CI95[2,0459940;2,3112817],2000draws/seed2026.
Đây là suy giảm validation giữa hai mốc đã quan sát trên một training seed;
không có nhánh continued-LM ngang chi phí để cô lập nguyên nhân, không có
khoảng bất định qua training seeds. Script mới chỉ là secondary diagnostic,
không mở gate viết cho checkpoint80M hoặc đổi lịch100M đã khai báo.

PPL cuối SFT được trainer ghi7,2114 trên12.192**response-only** targets là tập
mục tiêu khác; không dùng nó thay cho PPL general-text83,44. Kết quả không
thuận này phải theo cùng báo cáo sau này. Chưa thay threshold/seed, tăng cap,
đổi parent sang checkpoint được chọn sau kết quả, hoặc tuyên bố đã viết tốt.

## Tiếp tục đã được phép

Driver10, session `20261126T200540Z`, đã reserve trong ledger đọc lại độc lập,
T4,1100ssoftcap, UI588,69CU/rate1,87 lúc bắt đầu; cùng mount. Giữ cap16drivers
và16CU observed-drop từ anchor597,61, không mua thêm. Tiếp tục đúng minGRU
seed0; Transformer final/latest được kiểm unchanged trước launch.

Cell39 xếp read-only sau10: chỉ tái sử dụng proof của checkpoint byte-identical
với source/policy/proof hashes không đổi; checkpoint mới phải chạy diagnostic.
Kiểm final/latest tensor equivalence và tạo các phần ZIP để cloud readback;
không tự mở driver kế tiếp. Writing panel vẫn chờ cả hai parent100M và đủ34nhãn
tác giả thật theo rule đã chốt. Chỉ một người đọc hiện có, chưa xác nhận độc lập.
Post/seed mở rộng, transfer, primary test, manuscript có kết quả và LaTeX vẫn
chưa hoàn thành; không có mốc submitted/accepted/published.


## Secondary Drive reports: resolved

The52,667byte private bundle was directly uploaded and independently read back
with the Drive connector. Exact ZIP SHA
2fa9e3c7b21ea6771994666f6495a17367d94c90bd767c0f5b1827f7a6d9bd23
and all16members match the manifest. Code snapshot
822be6d97985d56951faed0c51e0717700d3203c is included. Private parent/shared=false
were verified; no new grant, credential storage or permission change. Earlier
local-only status is historical; the secondary reports are now on Drive.
