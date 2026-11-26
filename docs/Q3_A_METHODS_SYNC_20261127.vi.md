# Đồng bộ nguồn phương pháp Q3-A — 27/11/2026

Trong lúc lượt8 train, rà lại nguồn LaTeX và phát hiện phần implementation còn
mô tả byte259/context2048, warm-up5M và các backbone2,1Mtham số. Những giá trị
đó thuộc chuẩn bị cũ; chúng không mô tả foundation c18 đang chạy. Không sửa hay
loại các receipt/kết quả âm cũ. Nguồn draft hiện được đồng bộ với code/config
subword; **không chạy compiler hoặc render PDF**.

Các thay đổi:

- Working title: *Learning When Premise Changes Preserve Narrative
  Consequences*. Đổi tên để phân biệt giữ hệ quả bắt buộc với ép nguyên đoạn
  truyện không đổi. Câu hỏi A1−A2 vẫn giữ, không thêm claim kết quả.
- Corpus300k train/300validation/300test, tokenizer50257cố định, context1024,
  BOS/EOS/PAD50256, token0hợp lệ; masking theo nhãn/độ dài, EOS được chấm.
- Counts thật Transformer3.681.984/minGRU3.682.887; mô tả factorization/tiedhead,
  số tham số khác functional capacity, không dùng pretrainedLMweights.
- Foundation80M LM+20M SFT/parent, lịchLR/optimizer reset đúng config. Matrix
  pilot2M×24 vẫn cần6parents thật; confirmation ceiling10M/run cũ còn có điều
  kiện, chưa ngân sách/chạy. Không thay toàn bộ confirmation bằng pilot nhỏ.
- BackendCPU/FP64 trước primary outputs và FP32failure cũ; actual train giữFP32.
  Formula chính `Y_s=(S_bS_e+S_bS_n)/2`, source uncertainty conditional trên
  seeds, PPLfull-vocab gồmEOS và bootstrap theo truyện. Chưa nhãn người/primary.
- Giới hạn generator: thiếu equality tại deadline và double-blocker. Transfer
  ngoài template chưa validated. Không nhận stories/JS/no-op đơn lẻ là novelty.
- Recheck primary metadata/abstractPASTA/CFI/CSR, bổ sungCSR citation chính xác.
  CFI dùng group-level reward/policy gradient; A3 không tái lập toàn hệ ấy hoặc
  fullCSR. DTOđã đọc chọn lọc; không tuyên bố full-text audit mọi nguồn.

Rà static môi trườngLaTeX/braces/citation keys/JSON đã đạt; không phải build,
layout review hoặc quyết định bài đủ chuẩn journal. Không có result table đã
sinh trong paper directory. Tác giả vẫn trống, results shell vẫn trống. Dùng
hướng dẫn biên tập cài đặtTurnitout Humanizer cho rõ nghĩa; không dùng proprietary
engine, không tuyên bố detector/plagiarism score hay tạo nhãn người.

## Quan sát phần cứng và sửa evidence board

CIM báo AMD RyzenAI5 340,6cores/12logical, RAM16.418.648.064bytes. PyTorch local
`2.10.0+cu128` báo CUDAavailable, NVIDIA GeForceRTX5050LaptopGPU với
8.546.484.224memorybytes. Lưu `configs/q3a/local_hardware_observation_20261127.json`.
Đây là query phần cứng,0optimizer, **chưa đo** local research-training throughput;
không tự chuyển scientific training từ Colab sang local hay giảRTX3060.

`configs/q3a/evidence_gates.json` trước đây còn các giá trịcurrent của lượt1–3
và byteplan. Đã sửa current vềc18/audit7/live8,233nontrainingtests và16requirements;
giữ byte calibration/blocked audit cũ dưới historical fields. Board tự nó không
chứng minh completion. Các gate còn thiếu gồm đủparent, writing/human evidence,
seed plans mới, measured study budget, confirmation decision, novelty/transfer,
testregistration/primaryresults, manuscript với kết quả và cuối cùng mớicompile.

Không đổi foundation source, permission, optimizer, data hoặc cap đang chạy.
