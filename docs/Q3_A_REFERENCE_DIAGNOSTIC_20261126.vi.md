# Q3-A — đối chứng tham chiếu và profile tokenizer, chưa train thêm

26/11/2026, sau khi calibration2 không đạt writing gate. Đây là chẩn đoán cục
bộ, không phải kết quả chính hoặc đối chứng đã khớp điều kiện cho paper.

## Nguồn và phép đo thật

Đã tải riêng checkpoint tác giả
[TinyStories-1M](https://huggingface.co/roneneldan/TinyStories-1M/tree/77f1b168e219585646439073245fe87e56b3023e),
revision `77f1b168e219585646439073245fe87e56b3023e`. Sau khi instantiate và
load bằng Transformers, số tham số thực **3.745.984**, trong đó token embedding
**3.216.448**. Không dùng tên “1M” làm số đếm. Config: width 64, 8 tầng,
16 heads, vocab 50.257, giới hạn vị trí cấu hình 2.048. Giới hạn này không
xác minh context thực đã dùng khi tác giả train hoặc full training schedule.

Dùng tokenizer được model card hướng dẫn:
[EleutherAI/gpt-neo-125m](https://huggingface.co/EleutherAI/gpt-neo-125m/tree/21def0189f5705e2521767faed922f1f15e7d7db),
revision `21def0189f5705e2521767faed922f1f15e7d7db`. Card tại revision này
ghi MIT; **không** chuyển license này sang trọng số TinyStories. Card của
TinyStories-1M không nêu license trọng số ở metadata đã kiểm; chỉ giữ bản tải
cục bộ để chẩn đoán, không phân phối hoặc dùng làm training parent.

Weights 48.578.813 byte, SHA256
`07f9609ea882b8163ff3b23d40e2b82cb715d409631beb15c84b164f3877dae7`.
Không có learned tensor thiếu hoặc lệch shape khi load. 16 key dư chỉ là causal
mask/negative-mask buffers của Transformers cũ; code chặn mọi key dư khác.

## Thực thi và giới hạn diễn giải

Giữ toàn bộ 16 prefix đã dùng trước đó; chốt trước output hai dạng prefix
trực tiếp và prefix + instruction. Mỗi dạng một sample/source, temperature 0,8,
top-k 40, seed 17, tối đa **128 subword tokens**. Đã sinh đủ **32** đoạn bằng
CPU 2 threads, PyTorch 2.10.0+cu128/Transformers 5.24.1; generation loop đo
17,647 giây, không gồm tải/cài/import/load. Không optimizer hay fit tokenizer.
Sau tải input, chạy offline/local-files-only, không gửi prompt tới inference API.

Mỗi dạng có 16 chuỗi output khác nhau; 11/16 prefix-only và 5/16 dạng instruction
chạm cap 128 token. Không gọi chạm cap là EOS hoặc điểm fluency. Đã đọc cả32:
nhận xét assistant thấy câu chữ dễ đọc hơn các sample byte LM, nhưng còn lỗi
ngữ pháp, sự kiện/nhân vật thiếu liên kết và không ổn định yêu cầu 3–5 câu.
Không gán điểm người thật hoặc nhận đã có một positive control đạt mọi tiêu chí.

Đối chứng này khác số tham số, tokenizer, dữ liệu/schedule pretraining và token
unit; overlap với nguồn kiểm tra chưa được xác minh. Vì vậy nó không định lượng
lợi ích tokenizer, không bác bỏ bài TinyStories, không tái lập GPT-Eval của bài,
không thay thế baseline chính và không chứng minh model ta đã sẵn sàng viết/chat.
Tất cả human labels vẫn null; không mở final test.

## Tính tái lập trên Windows

- Runtime Transformers cài vào artifact target riêng; main venv vẫn có
  huggingface-hub 1.33.0/fsspec 2026.2.0. Pip báo dependency warnings giữa runtime
  target mới và datasets ở base environment; chẩn đoán không import datasets.
  Không gọi toàn bộ dependency stack là đã được xác minh cho training.
- Startup đầu dừng trước generation do API mới trả set trong loading report;
  đã chuẩn hóa sang sorted lists. Giữ tệp setup chưa hoàn tất; lần v2 sinh đủ
 32 samples theo cùng protocol, không đổi decoding để chọn output đẹp.
- Provider có hai tên `README.md`/`readme.md` khác nhau. Windows local-dir có
  thể đụng tên; đã tải file chữ thường vào thư mục riêng, đúng 811 byte/SHA
  `422ef5c71de03b225c364278eb6c173009f8655720dee2993870310022ab4f4c`.
  Receipt cũ ghi 710 byte được sửa rõ; model config/weights không bị đụng tên.
- Public recipe chỉ lưu source IDs và hashes; prompt/corpus text, output và
  weights nằm trong ignored artifacts. Helper tái dựng private manifest đúng
  SHA `2ec5e6d8dc78e1e4e7f30c26dbd889172804d6d56b58ce698f0b4e5fab9f5672`,
  kể cả CRLF của bản khai báo trước generation.

Tái dựng protocol, không generation:

```powershell
.venv/Scripts/python.exe scripts/prepare_q3a_reference_protocol.py --recipe configs/q3a/reference_inference_recipe.json --corpus data/raw/q3a-tinystories-calibration2.jsonl --output artifacts/reference-protocol.json
```

Inference dùng `scripts/inspect_q3a_external_reference.py` với đường dẫn runtime,
model/tokenizer đã pin, private protocol và output mới. Output v2 SHA256:
`dc958a20a7bc55020d6162daf0ee90b84c111f118bd6ce3a19c84a451849e47e`.

## Profile chỉ trên 30.000 truyện train

Giữ nguyên tokenizer đã phát hành, không pruning/fitting. Encode/decode round
trip đúng cả 30.000 truyện train. Không tokenize validation/test để chọn context
trong phép profile này.

| Đại lượng | Đo thật |
|---|---:|
| UTF-8 bytes, chưa thêm special tokens | 27.415.677 |
| BPE tokens, chưa thêm special tokens | 6.819.822 |
| Byte/BPE-token | 4,019999 |
| Input length gồm BOS p50/p95/p99/max, nearest rank | 196/468/670/1.064 |
| Truyện quá 512 / quá 1.024 input tokens | 1.015 / 16 |
| Suffix instruction chung | 63 byte / 15 BPE tokens |

Đây là lý do kỹ thuật để **xem xét** nền subword và exposure theo văn bản cho
pilot thay thế: số bước hồi quy/độ dài token khác đáng kể. Không coi compression
ratio là bằng chứng tăng chất lượng hoặc lợi ích MIM. Không so PPL giữa hai
tokenizer như cùng đơn vị, không âm thầm bỏ truyện dài để báo chất lượng cao.

Chưa cấp run mới: calibration2 vẫn dừng ở 3/3 lượt. Trước optimizer tiếp theo
cần amendment mới với một phương án nền ngôn ngữ có giới hạn, parameter counts,
input/target accounting, source split, resource gates và code checks đầy đủ.
Không mở A0–A3/B/C/Q1, compile LaTeX hoặc đánh dấu goal complete từ chẩn đoán này.
