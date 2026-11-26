# Q3-A: kết quả pilot Colab đầu tiên — 26/11/2026

**Đã train thật hai warm-up seed 0; chưa chạy điều kiện A0/A1/A2/A3.** Khả năng
viết chưa đạt ở các mẫu kiểm tra, nên chưa mở rộng post-training. Đây là kết
quả calibration ban đầu, không phải kết luận về giả thuyết selective consequence,
không phải đánh giá người thật và chưa đủ để nhận đạt chất lượng Q3.

## Điều kiện đã quan sát

Tài khoản Pro+ đúng yêu cầu; Drive đã mount, ghi/đọc thử và nhận bundle đúng SHA.
T4, High-RAM tắt, float32, Python 3.13.16, PyTorch 2.14.1+cu130, CUDA 13.0.
Mỗi mô hình dùng tokenizer byte 259, hai tầng, batch 2, context 2.048, AdamW
LR 0,0003 và cùng thứ tự nguồn/target budget. Các file environment ghi chi tiết.
Đây là minGRU và Transformer; chưa train kiến trúc MIM trong pilot này.

| Chỉ số đo thật | minGRU | Causal Transformer |
|---|---:|---:|
| Số tham số thực | 2.099.864 | 2.119.408 |
| Run ID | `warmup-mingru-s0` | `warmup-transformer-s0` |
| Supervised target tokens | 5.000.000 | 5.000.000 |
| Input tokens đã xử lý | 5.000.318 | 5.000.318 |
| Số cập nhật | 4.400 | 4.400 |
| Thời gian cập nhật trọng số, giây | 136,837 | 85,933 |
| Thời gian validation tích lũy, giây | 21,189 | 16,067 |
| CE tốt nhất trên **mixed warm-up validation** | 1,07323 | 1,95596 |
| CE trên **original general validation** sau train | 1,16332 | 2,14498 |
| PPL trên original general validation | 3,20055 | 8,54191 |

Mixed validation có 308.953 target labels, gồm truyện gốc và ví dụ instruction
phái sinh; general validation chỉ dùng truyện gốc, 250.090 target labels. Hai
phép đo có corpus khác nhau, không đổi tên best mixed CE thành general-text PPL.
CE là trung bình `-log p(token tiếp theo)` theo target label, đơn vị nat;
PPL = exp(CE). Tokenizer này tính byte cùng EOS, không phải perplexity theo từ
và không so trực tiếp với PPL của tokenizer khác. PPL thấp chưa bảo đảm văn xuôi
đúng ngữ pháp, theo được prompt hoặc hợp logic.

Driver chạy 296,443 giây cho cả hai warm-up, dưới cap 600 giây đã chọn. Đây
không phải toàn bộ thời gian thuê GPU: còn allocation, mount, bootstrap, kiểm
tra, inference và thao tác UI. Peak allocated quan sát qua các chunk khoảng
0,600 GiB/minGRU và 0,746 GiB/Transformer; không phải tổng VRAM runtime.

Giao diện báo 599,49 CU trước công việc GPU; T4 khoảng 1,24 CU/giờ, CPU khoảng
0,08 CU/giờ. Lần đọc cuối trước disconnect là 599,25 CU. **Chưa có số debit
quyết toán cuối**, không lấy chênh lệch này làm toàn bộ chi phí phiên. Runtime
đã được quan sát ngắt trước 16:15:42 giờ Việt Nam; UI bắt đầu GPU ở phút 15:57.
Không mua thêm CU hoặc subscription. Không dùng throughput warm-up để khẳng định
thời gian post-training/A3: số input/prompt/probe trên mỗi target khác nhau.

## Khả năng viết: gate chưa đạt

`scripts/inspect_q3a_warmup.py` chọn prompt trước khi xem output: một yêu cầu
viết ba câu và hai prefix từ original validation, chọn theo source ID với điều
kiện cú pháp/cỡ context được ghi trong mã. Chính sách giải mã giữ nguyên:
temperature 0,8, top-k 40, seed 17, tối đa 512 token mới; không thử nhiều seed
rồi chỉ giữ đoạn đẹp. Không mở test, không cập nhật trọng số trong inspection.

Đã lưu đủ sáu output, token IDs và provenance. minGRU sinh **cùng nguyên văn**
cho cả ba prompt, đều chạm 512 token. Transformer có ba output khác nhau;
hai chạm 512 token, một dừng ở 135 token. Tất cả qua kiểm tra UTF-8 của generator,
nhưng quan sát định tính cho thấy lỗi từ/ngữ pháp và đoạn bị cắt, chưa đáp ứng
mục tiêu truyện tự nhiên 3–5 câu có liên hệ với prefix. `human_label=null`
trong cả sáu bản ghi; không biến quan sát của agent thành nhãn/nghiên cứu người.

Điều này **không bác bỏ** giả thuyết A1−A2 vì chưa train hai điều kiện ấy.
Nó cho thấy khởi tạo ngôn ngữ hiện tại chưa đủ phù hợp để tiến hành phép đo đó.
Không chạy hết 24 điều kiện chỉ để có bảng số liệu khi writing gate còn thất bại.

## Kiểm tra triển khai sau train

- Bốn engineering fixtures đã đạt trên runtime CPU và trên máy ảo T4 mới
  (15,58/14,24 giây trong pytest); các fixture đó chạy model CPU, không tự
  chứng minh đường optimizer GPU. Các bước GPU thật có log hữu hạn và checkpoint.
- Kiểm tra checkpoint đã train trên T4, chuỗi 512 token: sai số lớn nhất giữa
  full cached-eval và từng bước là 7,63e-6/minGRU, 8,58e-6/Transformer; logits
  hữu hạn. Đổi token cuối không đổi logits trước đó. Đây là một chuỗi kiểm tra,
  không phải chứng minh cho mọi input hoặc mọi độ dài. Với Transformer, phép
  “full” ở đây cũng đi qua cached-eval, cần phân biệt với dense training path.
- Kiểm tra thêm trên CPU local/PyTorch 2.10.0+cu128 với trọng số thật: dense
  train-mode/dropout 0, dense eval và cached eval khớp trong sai số 4,77e-6 hoặc
  nhỏ hơn trên chuỗi 512 token. Không có optimizer update. Môi trường này khác
  Colab; chưa nhận đây là kiểm tra đầy đủ mọi kernel CUDA/PyTorch 2.14.

Chưa thấy lỗi shift/causality/cache trong các kiểm tra đã làm. “Thiếu học” và
“format warm-up chưa dạy tiếp nối có điều kiện” vẫn là **giả thuyết chẩn đoán**,
chưa xác định nguyên nhân. Ví dụ phái sinh hiện dùng yêu cầu viết truyện mới;
không tương đương huấn luyện tiếp một prefix có sẵn.

## Bảo toàn bằng chứng

Drive: `MIM-LLM/Q3-A/20261126-ba881daafbbd/`, gồm inputs, sessions, runs,
inspections và exports. Sau khi ngắt runtime, connector Drive đã đọc lại gói
46.329.484 byte từ cloud; tải về local và kiểm tra SHA gói cùng cả 27 file bên
trong. Do đó bằng chứng persistence không chỉ dựa vào cache DriveFS của VM cũ.
Đã xác minh 8.800 dòng metric đúng thứ tự update, target deltas cộng đúng budget,
CE/objective/gradient norm/time hữu hạn và cả hai checkpoint cuối có thật.

| Artifact | SHA256 |
|---|---|
| Transformer `final.pt` | `bff431959d4eeb17707d1b63c61b63fef14fd90a704349879aac75ed0990195a` |
| minGRU `final.pt` | `e366ae6e6a26e01af4ee79ba9cef1758c3d26793e5f3b19fd78a356a7e6e7c83` |
| Gói evidence ZIP | `3e9a2631cd851d873fc9a4917c7fa7857fbe89922f92faf8fb32c38c7303b8fe` |
| Mã inspection, normalized source | `5dea2e8830d1ee00e6a97e5cd649be0c7fe558d6f1a9ff30edc07248f62adb8f` |

Plan vẫn là
`ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142`;
bundle vẫn SHA `2ad7e8d63189ffc84b5802cf31df01950d596bc2d57021a56f8f9e7240ac6f2b`.
Trọng số, raw metrics/output và ZIP giữ trong Drive/local ignored artifacts;
không đưa lên GitHub, không ghi OAuth/signed download URLs trong repo.

## Bước tiếp theo, chưa thực hiện

Rà data/label alignment và mức học từ log thật; chốt **một sửa đổi calibration
có giới hạn** trước khi train thêm, gồm cách dạy continuation có prefix, lượng
corpus/training tokens và ngân sách đo được. Giữ toàn bộ held-out source groups,
đặc biệt test chưa mở; giữ tokenizer và decoding. Nếu đổi corpus/cap, tạo
manifest/plan/run authorization mới, giữ nguyên pilot cũ và công khai thay đổi;
không resume checkpoint như thể plan không đổi. Chỉ mở rộng post-training sau
khi khởi tạo đủ khả năng viết; nếu vẫn thất bại, sửa/thu hẹp nghiên cứu theo bằng
chứng, không lặp chọn seed/decoder đến khi có hiệu ứng thuận chiều.

[TinyStories gốc](https://arxiv.org/html/2305.07759) dùng GPT-Neo và tokenizer
khác cấu hình byte ở đây; thành công của họ không bảo đảm cấu hình pilot của ta.
Không dùng nhận định ấy để khẳng định một ngân sách sửa đổi chắc chắn thành công.
Human evaluation, primary condition results, transfer và manuscript có kết quả
vẫn chưa hoàn tất. Không compile LaTeX thêm theo chỉ dẫn của người dùng.
