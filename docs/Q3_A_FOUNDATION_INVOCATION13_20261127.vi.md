# Q3-A: hai parent seed 0 hoàn tất, 34 mẫu viết và kết quả retention — 27/11/2026

**Đã hoàn tất foundation seed 0; nghiên cứu chính chưa hoàn tất.** Driver 13
session `20261126T212456Z` kết thúc return code 0 sau 771,9626 giây, sớm hơn
soft cap 1.100 giây. Không chạy driver 14 hoặc post-training A0–A3.

| Backbone | Số tham số thực | LM targets | SFT response targets | Updates | Input tokens |
|---|---:|---:|---:|---:|---:|
| Transformer nhỏ | 3.681.984 | 80.000.000 | 20.000.000 | 216.366 | 113.197.507 |
| minGRU factorized, ứng viên tuyến tính | 3.682.887 | 80.000.000 | 20.000.000 | 216.366 | 113.197.507 |

Đây là hai baseline, không phải MIM hoặc full minGRU nguyên bản. Targets là
các vị trí được xử lý khi train, có thể lặp qua epoch, không phải số mẫu duy
nhất. Hai parent này là **2/6 parent** dự kiến nếu nghiên cứu đi tiếp đủ ba
seed; số post runs chính đã chạy vẫn **0/24**. Không suy từ pilot này ra năng
lực chat hoặc khả năng mở rộng của MIM-LLM.

## Drive và numerical evidence

Đã tải độc lập bốn phần ZIP qua connector, kiểm từng hash rồi ghép đúng archive
**359.097.282 bytes**. Audit lúc `2026-11-26T21:44:54.941765Z` xác minh
**149 members / 432.732 step metric rows**, counter theo pha và checkpoint
hashes. ZIP audit không load pickle. Bước load riêng các checkpoint có hash
được thực hiện với `weights_only=True`; final/latest của cả hai có cùng
identity, stats và mọi tensor model dù file serialization có hash khác nhau.

| Bằng chứng | SHA256 |
|---|---|
| Archive foundation cuối | `c615b69666103af6be123cd46967e7a29a1d56f679dc2bc87883a7f2f933b069` |
| Parts manifest | `73fc7cf79020d0cbd22f20d3ac15872feabcc1b84c76127ff533cd8396039913` |
| Transformer final | `30c5b6b8a8006f4ce1bc4a7d962adcbe0548b13eeb395daca1b8694647964c45` |
| minGRU final | `756a07755ab25149b3574af0f008ccbebdad3981e15f521e962727ea4100e0d9` |
| minGRU latest dùng trong proof | `ae544a4e1baee5dc2a136d9b63e04f0e7ed8234dadd37c6c696ecf072d5ead27` |
| Diagnostic index cuối | `e32a35c2b02403e385d3157cdce42e7ff9106c89e63efd84dbcea681b5663f71` |
| minGRU FP32 proof | `aa8778c0c26cebf7b871367881383945304bf8d400b2b578cffbc5a84ee55d6f` |
| minGRU FP64 proof trên Colab | `9b00a1c28934aaaddc960c4dd5153e25c260cca5884349dc5f953cb61b955a47` |

Proof mới của minGRU được đọc lại/hash-check và duyệt policy local. Proof
Transformer trên Colab chỉ tái dùng sau khi đối chiếu đúng weights/source/
policy/receipt, không gọi đó là diagnostic mới. Giữ mọi failure FP32 cũ.

Trước khi sinh mẫu ở Windows, đã chạy lại fixed validation-641/train-1024
FP64 panel trên Torch **2.10.0+cu128**, khác Colab **2.14.1+cu130**. Cả hai
đạt path, causality, reset và distribution bounds không đổi. Max path error
Windows: Transformer 1,06581e-13; minGRU 6,46982e-14; argmax khác 0. Các trường
FP32 training-flag trong proof FP64 được dẫn từ đúng proof Colab gốc, không
phải một lần train/gradient check mới trên Windows. Không có optimizer local.

## Perplexity trên cùng văn bản validation: kết quả âm cần giữ

Perplexity đo mức model gán xác suất cho các token đúng; với N token,
`PPL = exp(sum(token negative log-likelihood) / N)`. PPL thấp hơn nghĩa là dự
đoán tập token này tốt hơn. Nó không trực tiếp chấm một đoạn sinh trôi chảy,
theo prefix hoặc hợp logic.

Đo CPU/FP64 trên cùng **300 truyện / 61.573 BPE targets gồm EOS**, trước SFT
tại đúng boundary 80M và sau SFT tại parent đủ 100M:

| Backbone | PPL trước SFT | PPL sau SFT | NLL sau − trước, nats/token | Bootstrap CI 95% cho chênh NLL |
|---|---:|---:|---:|---|
| Transformer | 9,40945 | 83,43866 | +2,18240 | [2,04599; 2,31128] |
| minGRU | 11,56888 | 125,21978 | +2,38175 | [2,22693; 2,52019] |

Các khoảng này resample **truyện nguồn**, 2.000 draws/seed 2026, có điều kiện
trên một training seed và hai checkpoint đã quan sát. Không có đối chứng
continued-LM khớp ngân sách hoặc replication qua seed; chưa xác định nguyên
nhân của suy giảm likelihood. Không lấy PPL chỉ trên response SFT có prompt
để thay thế general bare-story validation, không chọn lại parent 80M để tránh
kết quả âm, và không gọi đây là điểm fluency/human evaluation. General test
và controlled primary test chưa được mở.

## Bộ mẫu viết thật, chưa có đánh giá người

Sinh đúng manifest đã chốt trước: **16 prompt có điều kiện + 1 vô điều kiện
cho mỗi model**, tổng **34 mẫu**, cùng CPU/FP64, temperature 0,8, top-40, seed
17 và cap 128 BPE tokens. Không sửa hoặc chọn lại output.

- Cả 34 mẫu sinh EOS; không output rỗng hoặc chạm cap.
- Mỗi backbone có 16 conditional continuations khác nhau theo bytes.
- Samples SHA256: `ec4d303335edfc0745c91d141d180679035732b4d32430ed43773829b7f7f764`.
- Packet JSON SHA256: `030f580e9f250392f204b3d1c6875200ba062d0774c8b7fae1ee4e8cf54c04a3`.
- Markdown hiển thị SHA256: `b64d36f0a07d333e81002887efee335a612289b707b0b4e3e0b06ffaec2d1944`.

Các số đếm này **không xác nhận** số câu, fluency, prefix-following, sự kiện
mới hoặc consistency. Phiếu CSV ban đầu được tổng hợp đúng **0/34 nhãn,
pending**. Cần chính người dùng đọc và điền theo hướng dẫn, giữ private key
đóng đến khi chấm xong. Chưa có người đọc thứ hai hoặc independent validation.

Presentation version 2 thêm Markdown đọc được từ output nguyên văn, kiểm
hash và so lại nội dung với JSON. 17 tests packet/decision và Ruff đạt; test
fixtures giả lập được tách khỏi output thật. Rule 12/16 theo từng model và
unconditional gate giữ nguyên. Pass nếu có sau này vẫn không tự cấp quyền
mở cả ma trận. Hướng dẫn: [author-reader guide](Q3_A_AUTHOR_READER_GUIDE.vi.md).

## Chi phí quan sát và lưu trữ sau release

Lượt 13 thêm 7.751.433 SFT response targets trong 648,4665 optimizer giây;
peak allocated cao nhất 236.497.408 bytes, không phải tổng VRAM. Tổng hai
parent ghi 11.623,2722 optimizer giây; tổng elapsed của 13 driver là
13.041,8159 giây. Các số này không bao gồm mọi thời gian review/idle và không
phải hóa đơn GPU-giờ. Transformer đã dùng L4 rồi T4; minGRU dùng T4. Không
dùng số thời gian khác phần cứng làm đối chứng cost-matched giữa backbone.

UI CU: 597,05 ở driver đầu và 585,57 trước release, observed drop khoảng
11,48; tính từ annex anchor 597,61 là 12,04, trong cap 16. Đây gồm cả khoảng
review/idle và chỉ là số dư UI, không là chi phí train quy kết chính xác.
Không mua CU, đổi subscription hoặc tự mở B/C/Q1.

Sau archive readback, Cell 43 flush Drive và gọi unassign; UI xác nhận
**0 active sessions / Not connected to runtime**. Request receipt được đọc
lại qua connector sau release. Mount Colab không được hứa tồn tại vĩnh viễn;
không giữ GPU idle vô hạn để tránh login. Drive connector tiếp tục ghi/đọc
thành công mà không grant mới.

Bundle thứ cấp riêng tư `20261127-foundation-complete-secondary-f033002.zip`
chứa panel/phiếu trống, báo cáo retention theo nguồn, numerical proofs và
source/config provenance, snapshot code `f033002bf42d91b019434cc2c20c33b4137f8abb`.
Upload từ Windows rồi raw-readback sau release: **113.194 bytes / 45 members**,
SHA256 `9068307232371de99f8faa88561921adc3e07b06c9c8f6ddb54d15c50dfda1f2`.
Tất cả 44 payload hashes được đối chiếu với manifest; shared=false.
Không đăng weights, raw samples, CSV/key hoặc ghi chép vault riêng lên GitHub.

## Gate còn thiếu

Nhãn tác giả thật là bước kế tiếp để quyết định feasibility. Các seed khác,
ngân sách toàn nghiên cứu, baseline/protocol cuối, transfer có human semantic
audit, đánh giá người đọc độc lập, primary runs/test và kết quả manuscript
vẫn chưa hoàn tất. Giữ stop/merge nếu lợi ích chỉ là template exposure hoặc
không có insight mới. LaTeX chưa compile và không có milestone submission,
acceptance hay publication. Goal vẫn active; pilot không chứng nhận chuẩn Q3.

Receipt công khai: [`foundation_invocation13_results.json`](../configs/q3a/foundation_invocation13_results.json).
