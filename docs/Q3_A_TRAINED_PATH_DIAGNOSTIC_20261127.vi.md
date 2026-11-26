# Kiểm tra đường tính trên trọng số đã học — 27/11/2026

Checkpoint Transformer baseline3.681.984tham số sau50.057.365LM targets,
SHA `466eaf6d56d38b033718f3451c4d0c3a701e66d42d7809881ffabe5fd9f4bb64`,
được trích đúng bytes từ archive lượt3 đã audit. Đây là parent **chưa hoàn tất**,
không phải kết quả viết hoặc primary Q3-A. Không optimizer/tokenizer fit/test.

Helper mới nằm ngoài fingerprint bất biến của foundation. Chọn ba cửa sổ
validation-LM dài nhất, tie theo index (207,87,174; dài641,575,549), kiểm các
prefix32/128/512 và batch padded641; thêm cửa sổ train-LM đầu tiên đủ1024
(index1260). Không ghép/repeat truyện giả để làm đủ context. So tại vị trí có
hiệu lực; không dùng dự đoán ở query padding làm thước đo.

Các đường tính: training_features+head, dense eval, full KV-cache, từng token;
sửa toàn bộ nửa tương lai và giữ nguyên shape/mask; fresh call reset. Kiểm
hash toàn bộ weights và checkpoint trước/sau. CLI giữ report rồi trả nonzero
nếu có mismatch; không biến một report thất bại thành giấy phép mở rộng.

## Quan sát thực trên CPU

Máy Windows: AMD Ryzen AI5 340/Radeon840M,6physical cores, RAM16.418.648.064
bytes; PyTorch2.10.0+cu128 chạy **CPU**,2threads. Chưa đo CPU train throughput.

| Điều kiện | Kết quả |
|---|---|
| FP32,atol=rtol=1e-4 | **Fail**: có vị trí ở641/1024 không allclose |
| FP32,max error ở token-step,1024 | 0,0003204345703125 |
| FP32,max train-features/dense error,1024 | 0,00026047229766845703 |
| Causality cả eval và train-features | max past error0 ở cả5cases |
| Reset và weight/checkpoint hashes | không đổi |
| FP64 chẩn đoán cùng trọng số ở641/1024,atol=rtol=1e-10 | cả2cases pass |
| FP64,max error của các đường tính đã đo | 6,092903959142859e-13 |

FP64 ở đây là nâng dtype của **cùng FP32 weights**, không retrain. Causality/
reset vẫn exact0, weights không đổi. Điều này phù hợp với sai số số học FP32;
chưa tự chứng minh mọi đường GPU hoặc mọi checkpoint đều đúng. Không nâng
threshold sau khi thấy lỗi để gọi report FP32 cũ là pass. Trước lượt train kế
tiếp cần kiểm lại trên T4 và giải thích mismatch; vẫn giữ tất cả receipt âm.

[PyTorch2.10 numerical accuracy](https://docs.pytorch.org/docs/2.10/notes/numerical_accuracy.html)
(tra27/11/2026) giải thích phép toán batch/slice có thể cho sai khác do thứ tự
tính và precision; không bảo đảm bitwise equivalence CPU/GPU hoặc giữa versions.
Đó là bối cảnh số học, không phải miễn kiểm tra implementation.

Receipt local/private: `invocation3-trained-paths-cpu.json`, SHA
`61fbea77efc4d5587eedb40a2f3780f4ba587c9032c592490163c3627cc1d66a`;
FP64 diagnostic SHA
`86164f9c59426523979bff762a4aaffc3f42a44ddd993bb6b7d6a07cd5614d01`.
Helper source SHA
`9e4ae9a63b0bee4903fa4e4eb35ed85c5eba2ef8a327a980652e99efb79fbf6a`.

## Phạm vi và kiểm tra tool

4nontraining tests pass: hai backbones, model/mode/gradient không đổi, có
fault-injection để phát hiện cache sai và future leakage, từ chối nonprefix
padding. Default suite210passed/18trainingdeselected; Ruff pass. Không dùng
test xanh trên model nhỏ để bác bỏ mismatch trên checkpoint lớn đã đo.

Lượt4 đã được launch trước phát hiện CPU này và vẫn bounded; chưa chạy lượt5.
Thay L4→T4 là chuyển máy trong feasibility, không tạo thí nghiệm khớp compute
hoặc chứng minh backbone tốt hơn. Báo GPU/version theo từng invocation;
contrasts post sau này phải chia sẻ parent thực trong từng seed/backbone.
