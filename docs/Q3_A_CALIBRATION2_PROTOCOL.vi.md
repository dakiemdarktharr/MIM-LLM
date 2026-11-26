# Q3-A: calibration ngôn ngữ lần 2 — chốt trước train

Ngày 26/11/2026. Đây là **một** sửa đổi sau pilot 5 triệu byte-target/model
không viết được đoạn tiếp nối đủ tự nhiên. Không thay câu hỏi A1−A2, không mở test,
không chọn cấu hình theo hiệu ứng mong muốn. Kết quả âm cũ giữ nguyên ở
[báo cáo pilot](Q3_A_COLAB_PILOT_20261126.vi.md).

## Thay đổi và phần giữ nguyên

- TinyStories cùng revision `f54c09fd23315a6f9c86f9dc80f725de7d8f9c64`,
  CDLA-Sharing-1.0; tăng train từ 3.000 lên 30.000 truyện. Giữ **nguyên từng
  hàng cũ**, gồm 300 validation và 300 test. Loại exact full-text hash của mọi
  nguồn cũ khỏi phần bổ sung. Chưa tuyên bố đã loại mọi near duplicate.
- Giữ original-story LM rows; thêm instruction viết mới ba câu và instruction
  tiếp hai câu prefix bằng ba câu kế tiếp. Tách câu máy theo quy tắc bảo thủ,
  bỏ trường hợp dấu ngoặc kép/viết tắt/ellipsis; không phải nhãn người thật.
  Mọi bản phái sinh cùng split với truyện nguồn. Không thêm benchmark state labels.
- Corpus mixed thực tế: 54.818/612/585 rows train/validation/test. Train gồm
  30.000 original + 12.440 unconditional + 12.378 conditional rows. Học CE
  next-token trên toàn hàng như trước, không đổi thành response-only loss.
- Giữ byte tokenizer 259 không fit, hai backbone và số tham số thực
  minGRU 2.099.864 / Transformer 2.119.408, context 2.048, batch 2,
  AdamW LR 0,0003, dropout 0, cùng seed 0 và chính sách giải mã đã chốt.
- Khởi tạo mới từ seed 0; **không** gọi tiếp checkpoint pilot cũ là cùng plan.
  Mỗi model 50.000.000 target labels; tổng calibration mới tối đa 100 triệu.
  Đây là budget calibration, chưa cho phép train toàn bộ ma trận mới.

## Giới hạn tài nguyên

Tối đa **3 lượt driver × 1.100 giây** cho hai warm-up seed 0, có lưu/khôi phục
Drive. Khi hết số lượt, dừng kể cả model chưa đủ token; không tự cấp thêm lượt.
Ưu tiên GPU T4/High-RAM tắt. **Sửa đổi tài nguyên trước optimizer mới:** Colab
đã báo không cấp được T4, nên cho phép fallback L4; UI L4 bắt buộc High-RAM
(switch bị disabled), cần ghi chi phí đi kèm. Chỉ chạy nếu rate UI đã đọc
không quá 6 CU/giờ và số dư ít nhất 10 CU; giữ cùng GPU class cho cả hai warm-up
mới. Ghi `resource-observation.json` trước train và ở từng session, không xem
ước tính UI là hóa đơn. Không dùng thông lượng T4 để gọi là đo được trên L4.
Tổng 3.300 giây driver
không phải GPU-hours đã trả: allocation/setup/inspection/Drive I/O cũng tiêu CU.
Mỗi GPU session đặt mục tiêu soft cap 20 phút; ngắt khi lượt driver và sync xong.
Không mua thêm CU và không chạy B/C/Q1 hoặc tokenizer fitting.

Thông lượng pilot suy ra thời gian **ước tính** cho hai model khoảng 37 phút
chỉ cập nhật trọng số, cộng validation/I/O; dữ liệu/độ dài mới có thể đổi thông
lượng. Không khẳng định từ trước 3.300 giây chắc chắn đủ. Tổng debit thực phải
đọc lại sau phiên; giá UI xấp xỉ 1,24 CU/T4-hour là quan sát của phiên trước.

## Kiểm tra sau calibration

1. Kiểm đủ target/update/log/checkpoint hashes và persistence từ Drive; báo
   cả model chưa hoàn tất. CE/PPL original validation báo riêng mixed validation.
2. Dùng lại script inspection đã thực thi, cùng prompt selection và decoding;
   giữ mọi output, token IDs và null human labels. Không thử seed/temperature
   để chỉ giữ đoạn đẹp. Các prompt cũ đã được nhìn nên kết quả là calibration.
3. Kiểm tra thêm 14 prefix validation tiếp theo theo cùng thứ tự nguồn trước
   khi nhìn output mới; báo cả lặp/ngắn/chạm cap/lỗi chữ và mức liên quan prefix.
   Đếm câu máy chỉ là chỉ số format; không tự biến thành fluency/human score.
4. Chỉ cân nhắc post-training sau khi kiểm tra khả năng viết có căn cứ. Không
   tự khởi chạy 24 run khi warm-up kết thúc. Không sửa giả thuyết từ test.
5. Nếu vẫn không viết được hoặc không dùng prefix, ghi failure và chẩn đoán
   định hướng dữ liệu/kiến trúc; không lặp thêm budget/seed đến khi A1 thắng A2.
   Mọi thay đổi sau đó cần amendment có lý do và giới hạn mới, không sửa lịch sử.

## Nguồn và identity

[TinyStories gốc](https://arxiv.org/html/2305.07759) dùng tokenizer GPT-Neo
với 10.000 token phổ biến và thiết lập khác byte LM ở đây. Không nhận kết quả
của họ là bảo đảm cho cấu hình của ta. Hai yếu tố corpus/format cùng đổi trong
calibration nên cải thiện, nếu có, không xác định nguyên nhân riêng của từng yếu tố.

Expanded corpus SHA256:
`22eb4bb062f6276548fb7c673304ff468f88179a2e43cca004da0015fca8727b`.
Mixed warm-up SHA256:
`a23917217e47bbb221a525b0cddab6bc8510240a541a23d720eda9fa57992b70`.
Data transformation normalized source SHA256:
`c8791c1fa2958505ee255161bebf303be19b686b4ce271f62ffde50edc4f22cf`.
Plan ID:
`ef827ca21a627ce714caaea1d0ab52b293f858e526e654358bbb633c36328660`.
Bundle hash được ghi trong `configs/q3a/calibration2_receipt.json` sau export,
trước optimizer; receipt nằm ngoài bundle để không tạo vòng tự băm.
Không compile LaTeX trong calibration; chưa có primary results/nhãn người.

## Đính chính thời gian sau lượt 1, không đổi input snapshot

Lượt 1: inner driver thực tế 1.108,341 giây so với `--wall-seconds 1100`;
wrapper quan sát 1.115,721 giây, gồm khởi động/kết thúc. Tham số này là
**soft wall cap**, kiểm tra giữa các bước/chặng; validation/checkpoint sync đang
thực hiện có thể kéo dài thêm. Không gọi 3.300 giây là hard cap thời gian thuê
GPU hay hóa đơn CU. **Số lượt tối đa ba** vẫn bị chặn bằng ledger. Giữ nguyên
protocol/source bundle đã dùng trên Drive; ghi rõ correction này sau đo.

## Sửa đổi portability trước optimizer tiếp theo

Sau lượt 1, Colab tự cấp T4 dù đã chọn L4; lượt VM dự phòng này chưa chạy
calibration driver và mount Drive timeout, đã được kết thúc. Không coi nó là
thời gian train bằng không chi phí: debit CU của allocation/setup chưa biết.
Để không phụ thuộc vào một GPU SKU không được bảo đảm, **thay yêu cầu cùng
GPU class** bằng resume có ghi rõ từng chặng T4/L4. Số target, tối đa ba driver,
tokenizer, corpus, optimizer, seed/RNG checkpoint và toàn bộ learning loop giữ
nguyên. Không nhận trajectory bitwise-identical qua hai GPU hay matched-compute
comparison giữa hai warm-up. Các arm so sánh sau này vẫn cần chung checkpoint
khởi tạo thực sự; báo GPU/giây/CU quan sát của từng chặng riêng.

Driver lưu GPU trong từng invocation và giữ lịch sử cũ. Bundle/manifest/script
được lưu bằng tên có hash để không ghi đè input phiên trước; archive bỏ ZIP lồng
nhau nhưng source ZIP riêng vẫn giữ trên Drive. Scientific plan ID không đổi vì
learning implementation/data/config không đổi; phiên bản orchestration mới có
bundle hash riêng, phải xác minh trước optimizer. Chưa dùng kết quả A1/A2/test
để chọn sửa đổi tài nguyên này. Rate UI <=6CU/giờ và số dư >=10CU vẫn bắt buộc.

## Correction: bản dự phòng khi resume, phát hiện trong lượt 2

Mã orchestration cũ khôi phục cả `previous.pt` xuống local. Khi sync theo thứ
tự tên file, bản local cũ này có thể ghi đè bản `previous.pt` vừa được xoay từ
`latest.pt` trên Drive. Vì vậy không nhận bản dự phòng ở lượt 2 là luôn thuộc
chặng ngay trước đó. Các SHA của `latest.pt`, metric/target và Transformer final
vẫn được kiểm tra; chưa phát hiện mất checkpoint chính hoặc sửa trajectory.
Giữ nguyên bundle đang chạy và mọi log cũ. Mã dùng cho lượt sau bỏ local
`previous.pt` khỏi danh sách upload; chỉ phép xoay remote latest được tạo backup.
Hai regression checks xác minh backup không bị tệp restore cũ ghi đè và sync
lặp không đổi backup. Không đổi learning code, plan, target hay ba-lượt cap.
