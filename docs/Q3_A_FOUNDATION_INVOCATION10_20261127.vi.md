# Q3-A: audit lượt 10 và tiếp tục lượt 11 — 27/11/2026

Session `20261126T200540Z` kết thúc return0 sau **1083,466/1100giây** soft cap.
minGRU factorized, ứng viên tuyến tính, **3.682.887tham số** đạt
**50.849.604/80.000.000LM targets**, chưa bắt đầu20M SFT,57.070updates.
Transformer **3.681.984tham số** giữ nguyên parent80M LM+20M SFT/216.366updates.
Cả hai là baseline, không phải MIM. Chỉ1/6parent dự kiến đã hoàn tất.

Lượt10 thêm33.496.499LM targets,37.572updates;972,931817optimizer giây,
khoảng34.428,41targets/optimizer giây. Driver wall time còn gồm I/O; diagnostic
và review nằm ngoài thời gian optimizer. Peak allocated1.715.918.336bytes
không phải tổng VRAM. Thông lượng SFT minGRU **chưa đo**, không ngoại suy LM
thành cam kết thời gian hoàn tất SFT hoặc cả bài. Chưa có hóa đơn CU quy thuộc.

## Đọc lại và kiểm hash

ZIP270.347.134bytes được lấy qua3phần đã kiểm hash; ghép khớp nguyên bản
`11ef3ec805b82e110be65cfec5044507c193380d74af152a2c0ba16bcac6649e`.
Manifest phần:
`ab1f46b139a4bbca50b37765838a9509078ed9ae2f6ac64b10da32f06101b2dd`.
Verifier độc lập kiểm **113members/273.436step rows** cùng stage/input/target
counters, resource annex, ledger và checkpoint hashes lúc2026-11-26T20:30:25Z.
Không load pickle trong bước ZIP audit. Mount giữ nguyên, không gọi đây là
kiểm sau release. minGRU latest:

`31dae33a16955115b00e48eb4644ce600a088b25901dc003680639f6d9892f41`.

Transformer latest/final byte-identical với audit9. Cell39 dùng lại proof9
chỉ sau khi kiểm hash checkpoint, policy/source và cả hai receipt không đổi;
không nói đã chạy diagnostic mới cho model không thay đổi. Kiểm lại mọi tensor,
identity/stats của final/latest bằng nhau, cấu hình/tokenizer ràng buộc bởi
cùng verified plan_id. Byte hash hai kiểu serialization vẫn khác nhau.

minGRU được kiểm mới trên fixed train1024/validation641 panel và policy
ca5621d4…: FP64 max logit path error **4,0856207e-14**, max top40L1
**1,0013244e-14**, argmax khác0. Loss/gradient FP32 khi đổi cờ MHA bằng nhau
bitwise; causality/reset đạt. Bounds1e-10/1e-4/0 giữ nguyên, không suy thành
chứng minh số học cho mọi văn bản hay điểm chất lượng viết. Receipt đã đọc lại
độc lập và local `check_review` đạt. Index:

`7eb36938326fc05c98d850e292473ff05de8a29adae20c300363e74d7d747314`.

Cell39 ban đầu chưa thực thi dù đã dự kiến xếp hàng. Sau khi quan sát kernel
Connected/rảnh, không Executing và output trống, đã phát lệnh read-only một lần;
không khởi động lại train10. Giữ rõ khác biệt giữa thao tác dự kiến và việc
đã quan sát. Các chẩn đoán không gọi optimizer hoặc mở test.

## Lượt 11

Để không phụ thuộc vào cell chờ riêng, source host của11 chứa driver1100giây
và phần read-only sau nó trong cùng một lần thực thi. Đã lấy source thật từ
notebook riêng tư trên Drive, kiểm AST và diff. Chỉ cập nhật run index, hash
checkpoint/receipt đã audit và CU quan sát; không sửa thuật toán hoặc core
training fingerprint c18. Source12.700bytes được upload vào inputs trên Drive,
đọc lại ở Colab và kiểm SHA trước exec:

`eda1e918d0b72ed3e6620880bb40d8fcc55530e72309414cff2fcfc08be50b55`.

Bản chuẩn bị5e48f79c… không chạy; đã thay trước launch để ghi đúng quan sát
CU mới587,75/rate1,87. Driver11 session **`20261126T203337Z`** live, ledger11
reserved được đọc lại qua connector. CùngT4/mount, không grant mới, cap16drivers
và16CU observed-drop từ597,61 giữ nguyên; không mua thêm. Phần read-only sau11
kiểm trọng số mới, proof tái dùng phải cùng hash, final tensor equivalence và
chia ZIP; không tự mở driver12. Chỉ gọi completion sau receipt thật và audit.

Kết quả âm general validation PPL của Transformer9,41→83,44 sau SFT vẫn giữ
ở audit9 và trên Drive, không chọn parent khác để né kết quả. Writing panel
vẫn chờ đủ2parent100M, sau đó cần34phiếu tác giả thật theo rule đã chốt; một
người đọc chưa xác nhận độc lập. Post/seed mở rộng, test, transfer, manuscript
có kết quả và LaTeX chưa hoàn thành. Không có mốc nộp/chấp nhận/xuất bản.
