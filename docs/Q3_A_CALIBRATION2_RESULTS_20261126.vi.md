# Q3-A — calibration2 hoàn tất, writing gate chưa đạt

Ngày 26/11/2026. **Không mở ma trận A0–A3.** Hai baseline đã đủ ngân sách,
nhưng 34 đoạn sinh cố định vẫn không chứng minh khả năng viết tiếp tự nhiên,
bám truyện. Đây là kết quả hiệu chỉnh và chẩn đoán; chưa có primary contrast,
human scores, final-test evaluation hoặc manuscript có kết quả khoa học chính.
MIM-LM chưa được train trong phép thử này; không suy luận lợi ích/tác hại MIM.

## Số đo thật

Plan: `ef827ca21a627ce714caaea1d0ab52b293f858e526e654358bbb633c36328660`.
Giữ tokenizer byte 259, split gốc, seed 0, giải mã temperature 0,8/top-k 40/seed
17/max 512 như protocol. Mỗi backbone đúng 50.000.000 supervised targets,
50.000.209 processed input tokens và 40.631 updates.

| Baseline | Tham số thực | Train giây | Validation giây | Best mixed CE | Original-validation CE | Original-validation PPL |
|---|---:|---:|---:|---:|---:|---:|
| minGRU | 2.099.864 | 1.075,405 | 154,002 | 0,858277 | 0,942140 | 2,565465 |
| Transformer | 2.119.408 | 571,104 | 95,246 | 0,976345 | 1,090014 | 2,974316 |

Train/validation giây là thời gian code đo, không phải toàn bộ giờ thuê GPU.
Transformer chạy L4; minGRU bắt đầu L4 rồi resume T4, nên không nhận một so sánh
matched-compute giữa hai backbone. Các arm sau này vẫn cần chung checkpoint
khởi tạo thực sự. Original-validation có 250.090 target labels gồm EOS, khác
mixed validation. PPL = exp(CE) tính theo byte-token; không so trực tiếp với
PPL theo subword hoặc dùng PPL thấp làm chứng nhận viết hợp logic.

So với pilot 5M, original-validation CE giảm ở cả hai model. Corpus, instruction
format và budget cùng đổi nên không gán cải thiện cho một yếu tố riêng.

## Toàn bộ 34 output và quyết định feasibility

Mỗi model: một prompt viết mới và 16 prefix từ validation; selection/decoding
đã chốt trước output calibration2. Giữ nguyên tất cả output, token IDs và null
human labels trong Drive/local archive. Không chọn seed hoặc đoạn đẹp.

- minGRU: 16 prefix chỉ cho **6 continuation khác nhau**; một đoạn lặp nguyên
  văn ở **10/16** prefix. Trong đoạn đó có câu “She loved to eat the park and
  books.” Mẫu ba câu về Lily xuất hiện cả khi prefix nói về nhân vật/chủ đề khác.
- Transformer: 16 continuation khác nhau, nhưng đọc cả tập vẫn thấy nhiều từ
  méo, câu thiếu liên kết và chuyển nhân vật thiếu căn cứ. Đa dạng chuỗi ký tự
  chưa chứng minh bám prefix. Một trong 17 output chạm cap 512 byte-token.
- Cả 34 output hợp UTF-8. Đếm câu máy: minGRU có 3 đoạn hai câu, 13 đoạn ba câu,
  1 đoạn bốn câu; Transformer có 7 đoạn hai câu, 6 đoạn ba câu, 3 đoạn bốn câu,
  1 đoạn tám câu. Đây chỉ là heuristic dấu câu, **không phải** điểm fluency/logic.

Kết luận writing gate chưa đạt là nhận xét kỹ thuật định tính của assistant sau
khi đọc toàn bộ tập; chưa phải đánh giá mù của người thật, tỷ lệ success hay
kiểm định thống kê. Không biến các nhận xét này thành nhãn người. Hiện chỉ có
người dùng sẵn sàng làm reader; chưa bố trí người thứ hai.

## Kiểm tra lỗi thực thi và chẩn đoán không train thêm

24 case trên T4/PyTorch 2.14.1+cu130 đạt: 3 truyện validation dài nhất × 4 độ
dài 32/128/512/1024 × 2 model. So dense train/dropout 0, dense eval, cached full
và từng token ở atol/rtol 1e-4. Sai số tuyệt đối lớn nhất 5,14984e-5; sửa token
cuối không làm đổi logits trước đó trong mọi case đã kiểm tra. Không gọi đây
là chứng minh không tồn tại mọi lỗi ở mọi độ dài hoặc phần cứng.

Chẩn đoán hậu nghiệm riêng bằng `scripts/diagnose_q3a_conditioning.py`, CPU
PyTorch 2.10, 2 threads, không optimizer/generate: giữ cùng reference tiếp theo
2–3 câu từ cả 16 nguồn đã chọn; đo CE response bytes, bỏ EOS nhân tạo khi cắt
reference. 96 forward cases hữu hạn và target accounting đúng.

| Model | Prefix + instruction | Chỉ instruction | Prefix trực tiếp |
|---|---:|---:|---:|
| minGRU | 0,904202 | 0,912265 | 0,907033 |
| Transformer | 1,011779 | 1,044899 | 1,013222 |

Đây là trung bình CE theo truyện của tập chẩn đoán, khác PPL toàn validation.
Bỏ prefix không cải thiện NLL; vì thế không nhận toàn bộ thông tin prefix đã
biến mất hoặc mọi logits giống nhau chỉ vì nhiều sample lặp. Đổi format/vị trí
cũng là nhiễu trong so sánh này. Chưa tách được thiếu exposure, tokenization,
exposure bias hoặc hạn chế kiến trúc; không chẩn đoán chắc nguyên nhân từ loss.

## Persistence, tài nguyên và lỗi backup đã sửa

Ba driver calibration hoàn tất return code 0, không có lượt thứ tư:

| Lượt | GPU | Inner driver giây | Wrapper giây | Trạng thái |
|---|---|---:|---:|---|
| 1 | L4 | 1.108,341 | 1.115,721 | Transformer đủ 50M; minGRU 17.865.693 |
| 2 | T4 | 1.111,539 | 1.120,870 | minGRU 49.847.937 |
| 3 | T4 | 48,049 | 57,173 | minGRU đủ 50M; thêm 4,787 giây train |

1.100 giây là soft cap; I/O/validation có thể vượt một ít. Allocation/setup,
inspection và thời gian chờ Drive không nằm đầy đủ trong bảng này. UI cuối
hiển thị 597,61 CU, rate 0 và **0 active sessions**; GPU đã được trả lại. Đây là
số dư quan sát, không phải hóa đơn hay phép gán toàn bộ debit cho optimizer.
Không mua CU, chạy B/C/Q1, fit tokenizer hoặc compile LaTeX.

Mã cũ có thể upload bản local `previous.pt` cũ sau khi xoay backup trên Drive.
Không phát hiện `latest.pt` chính bị sai. Lượt 3 dùng bản sửa; event xác nhận
backup mới đúng SHA của latest cuối lượt 2. Giữ nguyên nguồn/log cũ và correction
trong protocol. Full suite 166 nontraining tests/12 deselected đạt trước lượt 3;
hai regression cases bảo vệ rotation. Chẩn đoán CPU mới chạy thật và Ruff đạt.

Final archive đã được tải độc lập qua connector **sau khi runtime trả lại**:
52.053.267 byte, 53 member hashes và 81.262 metric rows liên tục/hữu hạn ở các
trường loss/gradient/time được kiểm; tổng target deltas đúng. Verifier không
giải nén hay nạp pickle. Sau đó giải nén an toàn vào thư mục artifacts mới để
đọc toàn bộ sample/report và dùng checkpoint cho chẩn đoán CPU.

| Artifact | SHA256 |
|---|---|
| Final evidence archive | `db500f041531cc797362e43691bf0c696da227f458c591ddb0e8c4b5d0904db1` |
| minGRU final | `7b9c8feffd4c9acec590cf488de81695558b4f5e3e6e6c32caae49cea66c6788` |
| Transformer final | `5db4e8d81ef58138a80268128c3414e45a354d7d1c3c2e80e8c5039a776316da` |
| Bundle thực thi lượt 3 | `14b762319ad9c1dab80407ff18437c1ed9e5ca57524ff17ad517735ed612e48b` |

Raw evidence, weights và dataset giữ local/Drive; GitHub nhận code và bản tóm tắt.

## Công việc tiếp theo và giới hạn claim

Không tự mở full matrix hoặc kéo dài calibration2. Giữ kết quả âm và chuẩn bị
phương án nền ngôn ngữ có căn cứ trước optimizer mới: kiểm tra một implementation
tham chiếu đã phát hành, đối chiếu tokenizer/corpus/schedule rồi chốt một thay
đổi có giới hạn với plan mới nếu thật sự cần. Không chỉ tăng budget/đổi decoder
đến khi thấy A1 thắng A2. Tokenizer fitting vẫn chưa được phép.

[TinyStories gốc](https://arxiv.org/html/2305.07759), footnote 2, dùng GPT-Neo,
window 256/context 512 và tokenizer GPT-Neo với 10K token thường gặp. Đây là
thiết lập khác byte LM hiện tại; chưa xác minh được full training schedule từ
đoạn nguồn đã đọc, nên không nêu số training tokens của họ. Model card
[TinyStories-1M](https://huggingface.co/roneneldan/TinyStories-1M) là ứng viên
kiểm tra tham chiếu, chưa được chạy ở đây; tên “1M” không thay cho phép đếm tham
số thực và quyền phân phối trọng số cần đối chiếu riêng.

Novelty vẫn theo [CSR audit](Q3_A_CSR_COMPARISON_20261126.vi.md); khả năng viết
không đạt không chứng minh hoặc bác bỏ A1−A2. Goal Q3-A vẫn **active/chưa hoàn
thành**: primary training, transfer, nhãn người, test, bản thảo có kết quả và
kiểm tra journal còn thiếu. Không tạo readiness receipt hoặc compile LaTeX để
làm thay các pha ấy.
