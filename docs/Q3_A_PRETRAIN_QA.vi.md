# Q3-A: biên bản kiểm tra trước train — 26/11/2026

**Trạng thái: chuẩn bị code/dữ liệu/draft, đang khóa train.** Người dùng chưa
cấp lệnh mới để cập nhật trọng số hoặc fit tokenizer. Không khởi chạy Colab.

| Phần | Kiểm tra thực hiện | Kết quả và giới hạn |
|---|---|---|
| Test suite | `.venv/Scripts/python.exe -m pytest -q` | **93 passed, 6 deselected**. Sáu case optimizer/overfit/resume/tokenizer fit chờ quyền train, gồm hai integration case mới của runner Q3-A. Non-training fixture chặn optimizer steps và SentencePiece fitting. |
| Permission | API cũ, runner mới và tokenizer fitter bị gọi khi khóa đóng trong unit test | Đều chặn trước train/I/O; không run ID hoặc plan ID nào được cấp quyền. |
| Objective | Shift/masking/padding, exact target cap, JS đối xứng/gradient hữu hạn, probe spans | Đã qua; chỉ backward, không optimizer step. |
| Model contract | Future-token causality, reset, full/step agreement; KV-cache chunk/padding trên CPU/CUDA | Đã qua. KV-cache không thêm tham số; đường train vẫn full causal forward. |
| Data | Semantic intervention, split/source/surface-family separation, exact duplicate rejection, hash/test integrity | Bộ cuối 6.000/400/400 source groups. Bốn duplicate draws bị loại. Các thư mục chuẩn bị thử trước bị thay thế, không dùng train. |
| Warm-up | Revision, license metadata, 3.000/300/300 nguồn, dedup, checksum | Đã tải TinyStories có pin/hash, chưa train. Không gọi đây là human-authored data. |
| Preflight | Cấu hình thực, batch hai; CE/JS backward và so sánh tham số trước/sau trên CPU và RTX 5050 Laptop | **0 optimizer steps, tham số không đổi**. VRAM đo là peak của preflight, không phải toàn bộ train hoặc tốc độ train. |
| Notebook | nbformat validation, execute cả 4 code cells bằng kernel local Windows/CPU | Không lỗi cell. Không có cell train; chưa chạy Colab thật. Local Jupyter phát host warnings; không suy ra tương thích toàn bộ Colab từ lần chạy này. |
| Local bundle | Zip manifest, giải nén sang thư mục khác, import source bên trong, load lại plan/hash | Đã qua; không lấy nhầm source từ editable install gốc. ZIP chỉ local, không Git. |
| Draft | Build cả bốn tài liệu; render/xem đủ 5 trang Q3-A, xem lại trang sửa cuối | Không lỗi/warning biên dịch, undefined refs, overfull hoặc underfull. Tác giả/kết quả vẫn trống; template journal chưa áp dụng. |

Đã kiểm tra **28 relative Markdown links**, **205 wikilinks trong 54 note
Obsidian**, notebook source không chứa outputs đã chạy và policy vẫn false
với danh sách authorized run/plan IDs rỗng. Git không stage PDF, weights,
ZIP, raw datasets hoặc private vault notes.

Hai cấu hình vận hành: minGRU width 662 **2.099.864** tham số; Transformer
width 248 **2.119.408** tham số; byte vocab 259, context 2.048, hai tầng.
Context lớn nhất cần cho prompt cộng reserve sinh trong bộ chuẩn bị là **1.476**.

Đã đối chiếu thứ tự source và reference targets của A1/A2: giống nhau tại
từng vị trí, nên source/target CE exposure của primary contrast được khớp.
**Chưa khớp chính xác lexical edit distance:** paraphrase đổi nhiều wording hơn
numeric no-op. Phải báo residual này, không gọi đây là control khớp tuyệt đối
hoặc suy một hiệu ứng thuần semantic mà chưa kiểm chứng thêm.

Plan ID:
`c0d50e6062189dea5ed1ee3a50c3a220e18093d20eca5b030d4ac673057db47e`.
Snapshot công khai: [prepared_snapshot.json](../configs/q3a/prepared_snapshot.json).
Nguồn code/input được fingerprint; thay đổi phải chuẩn bị plan mới, không resume
lặng lẽ. Hash nguồn code chuẩn hóa newline cho Windows/Colab.

Bundle local `artifacts/q3a-pretrain.zip`, 2.469.605 bytes, SHA-256:
`fb61aff78e20055d3ea3b34961e28e26bf73c44cae160cd5da79974b74235aa4`.
Không có weights mới hoặc nhãn người thật trong bundle. Những annotations/weights
giả lập cho unit test chỉ ở thư mục test tạm, không dùng làm dữ liệu nghiên cứu.

Các cổng khoa học/tài nguyên còn mở: usefulness threshold và registration trước
test; nguồn/cặp chuyển giao naturalistic có giấy phép và audit; hai người chấm
mù; throughput/CU trên Colab; optimizer/memorization/training-resume integration
sau lệnh cho phép. Gói $50 là thông tin người dùng cung cấp; exact SKU/credit
balance/rate chưa xác minh. Không có căn cứ nói đã đủ chi phí hoặc paper-ready.

Không có kết quả khoa học mới, train, human labels, submission, acceptance hoặc
publication. [Runbook](Q3_A_PRETRAIN_RUNBOOK.vi.md) phân biệt các bước chuẩn bị
đã chạy với lệnh được viết sẵn cho giai đoạn sau.
