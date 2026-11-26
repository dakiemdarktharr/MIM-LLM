> **Chỉ dẫn mới nhất 26/11/2026:** chỉ compile LaTeX sau các pha dữ liệu/train/test/phân tích có kết quả thật; [quy tắc và khóa build](MANUSCRIPT_PHASE_ORDER.vi.md). Q3-A được phép train có giới hạn trên Colab, đang chờ quyền Drive; B/C/Q1 và tokenizer fitting chưa được phép. [Scope hiện hành](SCOPE_REVIEW_BEFORE_TRAIN_20261126.vi.md) dùng numeric irrelevant-clock control cho A2, thay punctuation control cũ. Các hold/cấu hình/artifact dưới đây được giữ như lịch sử, không dùng để resume plan cũ.

# Q3-A: bộ chuẩn bị tới trước huấn luyện

Ngày 26/11/2026. Người dùng đã mua gói Colab giá $50 theo thông tin tự cung cấp;
chưa xác minh tên gói, số CU còn lại hoặc GPU/CU mỗi giờ. **Chưa được phép train
bất cứ mô hình hay tokenizer nào.** Không mở runtime Colab trả phí trong phiên chuẩn bị.

## Nội dung đã triển khai

Đề tài: *Learning When a Premise Change Should Not Change a Story*. A0 chỉ cặp
effective; A1 thêm semantic no-op; A2 thêm paraphrase; A3 dùng dữ liệu như A1 và
JS trên factual probe spans. Primary contrast là **A1−A2**. Mỗi arm nhìn cùng
source pool, cùng tokenizer, policy optimizer/decoding và trần response targets.
Chất lượng, độ dài, số lần lặp và processed input/probe tokens phải báo riêng.

Luồng: nguồn/corpus có provenance → bundle bốn biến thể → kiểm tra semantic và
split → plan có hash code/input → preflight không cập nhật → **DỪNG CHỜ LỆNH**
→ khi được phép: warm-up/kiểm tra optimizer/overfit/resume → post-training →
validation generation → freeze selection → test generation → hai người chấm mù
→ adjudication → source-paired bootstrap → bảng LaTeX từ kết quả thực.

Tokenizer vận hành là UTF-8 byte cố định, **259 IDs**, không fit tokenizer.
Đây là thay đổi được ghi rõ so với bản đếm thử BPE-512/context-256 trước đây.
Context hiện tại 2.048; minGRU width 662 có **2.099.864** tham số, Transformer
width 248 có **2.119.408** tham số. Chênh lệch khoảng 0,93%; không nói bằng tuyệt
đối. Hai model đều hai tầng, dropout 0. Chưa huấn luyện các cấu hình này.

## Dữ liệu và tính toàn vẹn

- Bản kiểm soát: `data/processed/q3a-final/`, 6.000/400/400 source groups cho
  train/validation/test; mỗi source có base/effective/no-op/paraphrase.
- Các cặp effective đổi **đúng một** tiền đề: giờ điện hoặc permission để đổi
  hành động đúng. No-op đổi giờ điện trong cùng vùng quyết định; giờ thực vẫn
  đổi, không ép toàn văn giống nhau. Có cancelled plans và 1–6 key transfers.
- Loại exact duplicate base prompts; kiểm tra không trùng source/surface family
  giữa split. Đây là bốn renderer của **một họ bài toán**, chưa phải transfer
  đa miền. Số bản draw bị loại và hash được ghi trong manifest.
- Warm-up: `data/raw/q3a-tinystories.jsonl`, 3.000/300/300 nguồn. Revision
  `f54c09fd23315a6f9c86f9dc80f725de7d8f9c64`; dataset card ghi
  [CDLA-Sharing-1.0](https://huggingface.co/datasets/roneneldan/TinyStories).
  Không gọi TinyStories hoặc template do máy tạo là truyện do người viết.
- Gold state/probe chỉ dùng ở train/scoring. Generation chỉ nhận prompt văn bản.
  Mandatory mentions tách khỏi mọi fact còn đúng; không chấm thiếu khi một fact
  không được yêu cầu nhắc. Nội dung mới của mô hình được người chấm kiểm tra.
- `test.lock.json` khóa integrity; chưa phải preregistration. CLI test còn yêu
  cầu freeze checkpoint/decoding/rationale từ validation trước khi mở test.

## Chuẩn bị lại trên Windows hoặc CPU Colab

Từ root repo, dùng Python 3.11+; notebook/requirements cũng có trong repo.
Các lệnh sau **không huấn luyện**, không tự ghi đè thư mục/plan đã tồn tại:

```powershell
.venv/Scripts/python.exe -m pip install -e ".[test,data,notebook]"
.venv/Scripts/python.exe -m mim_llm.q3a.cli prepare --output data/processed/q3a-final
.venv/Scripts/python.exe -m mim_llm.q3a.cli fetch-warmup --output data/raw/q3a-tinystories.jsonl
.venv/Scripts/python.exe -m mim_llm.q3a.cli plan --data data/processed/q3a-final --warmup data/raw/q3a-tinystories.jsonl --output artifacts/q3a-pretrain-20261126/plan.json
.venv/Scripts/python.exe -m mim_llm.q3a.cli preflight --plan artifacts/q3a-pretrain-20261126/plan.json --output artifacts/q3a-pretrain-20261126/preflight.json --device cpu
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/export_q3a_bundle.py --plan artifacts/q3a-pretrain-20261126/plan.json --output artifacts/q3a-pretrain.zip
```

Nếu artifact đã có, verify/load nó; không xóa hoặc ghi đè chỉ để chạy lại. Dữ
liệu ở các thư mục thử chuẩn bị trước `q3a-final` không phải bản được chọn chạy.
`load_plan` đối chiếu code fingerprints chuẩn hóa newline để dùng được giữa
Windows/Colab; thay code/input phải chuẩn bị lại plan, không resume lặng lẽ.

Mở `notebooks/Q3_A_Prepare_Colab.ipynb`, giữ runtime CPU, tải bundle local lên
`/content/q3a-pretrain.zip`. Notebook kiểm tra zip/hash và preflight; **Run all
không có cell train**. Agent chỉ kiểm tra notebook trên máy local; chưa chạy
Colab thật. Muốn giữ checkpoints sau khi được phép train, chọn vị trí Drive
persistent rồi truyền `--output-root`; không dựa vào ổ VM tạm của Colab.
Theo [Colab FAQ](https://research.google.com/colaboratory/faq.html), runtime có
thể kết thúc và loại GPU/tài nguyên không được bảo đảm. Không suy gói $50 đủ
24 runs khi chưa đo throughput và CU trên GPU thật.

## Các lệnh đã chuẩn bị cho giai đoạn sau — chưa được chạy

`configs/training_permission.json` đang false và không có run ID được phép.
Cả API train cũ, tokenizer fitter và runner mới đều chặn trước optimizer/I/O.
Không có lệnh tự unlock. Chỉ sửa permission và exact run IDs sau chỉ dẫn mới
của người dùng. Ví dụ cú pháp, **không phải lệnh được cấp quyền**:

```text
python -m mim_llm.q3a.cli train --plan PLAN --run-id AUTHORIZED_RUN_ID --output-root PERSISTENT_RUNS --seconds-limit USER_APPROVED_LIMIT --device cuda
```

Runner có target cap chính xác, time-limit từng invocation, AdamW, CE/JS,
gradient clipping, atomic latest/best/final, RNG/order/cursor, input/code checks
và resume. Time limit có thể vượt một update/validation/save đang chạy; đây
không phải hard billing cap. Cần theo dõi CU/runtime thực và ngân sách toàn
study qua nhiều invocation; không dùng resume để bỏ qua cap.

Sau khi đủ validation, chuẩn bị `freeze-selection`, `generate`, `perplexity`,
`blind-packet`, phân tích và `results-table`; xem `--help` của từng
lệnh. Test general-text PPL chưa có auto release; trước mắt chỉ validation PPL.
Test generation chỉ chấp nhận checkpoint hoàn tất đủ budget, đã freeze hash.

**Cập nhật 26/11:** dùng `python -m mim_llm.q3a_reviewed_analysis` cho nhãn
Q3-A. [Analysis review](Q3_A_ANALYSIS_REVIEW.vi.md) quy định trung bình hai
reader, panel source/seed đầy đủ và đăng ký SHA phân tích trước test. Lệnh
`analyze` cũ được giữ để tái lập phiên bản đã khóa, có hạn chế coverage/fluency
lấy reader A nếu không có phân xử. Không dùng đầu ra cũ làm báo cáo quality mới.

`freeze-selection` yêu cầu đủ 24 checkpoint post-training và file registration
có đúng plan ID, primary contrast, smallest useful effect, cap GPU-giờ và danh
sách source test chọn trước generation. Dùng
`configs/q3a/preregistration.template.json` làm mẫu; các ô null chưa phải đăng ký.
Đây là khóa nội bộ, không tự tạo chứng nhận đăng ký công khai. Generator test
chỉ chạy danh sách source đã khóa, giữ cả ba biến thể cho mọi system/seed.
Các kiểm tra vocabulary/state hoặc selection sơ bộ dùng validation, không
unlock test để thử nhanh một seed.

Transformer có đường KV-cache ở eval để tái sử dụng key/value giữa các token;
cache được đối chiếu với full forward, chunking và padding trên CPU/CUDA.
Huấn luyện vẫn dùng full causal forward. Bộ nhớ cache tăng theo context, không
gọi đây là constant-memory. Cơ chế mask tham chiếu
[PyTorch 2.10 SDPA](https://docs.pytorch.org/docs/2.10/generated/torch.nn.functional.scaled_dot_product_attention.html).

## Thước đo và nguồn lực

Mỗi continuation có success khi đúng mọi mandatory proposition, đúng format
3–5 câu và không mâu thuẫn. Mỗi source lấy trung bình joint success của
base/effective và base/no-op; hai pair kinds có trọng số bằng nhau. Bootstrap
paired theo source, giữ các pair/output/seed cùng cụm, báo từng training seed.
CI này có điều kiện trên seed đã quan sát; không chứa đầy đủ bất định tối ưu.

Hai reader chấm độc lập, khóa hệ thống được giữ riêng. CSV để trống; thiếu
nhãn/evidence bị từ chối. Có per-proposition accuracy, contradiction/type,
coverage, fluency, unclear, raw agreement/kappa và adjudication. Unclear giữ
trong denominator như failure bảo thủ. Không dùng regex làm primary oracle.
Để giảm công sức, chọn sample nguồn/cặp đại diện cân bằng và khóa sample **trước
generation/chấm**, không chọn câu hay sau khi xem output. Cỡ mẫu/nhân lực và
smallest useful effect chưa được phê duyệt; đây là scientific gates còn mở.

Pilot: 24 post runs × 2M = 48M response targets. Sáu warm-up × 5M = 30M
physical targets; các bài khác chỉ được credit warm-up khi thật sự dùng cùng
checkpoint/tokenizer/corpus/config. Nếu chạy A độc lập, phải báo đủ 30M warm-up,
không nhận sharing chưa xảy ra. Selection reserve 7,2M chưa chi. Ba Q3 vẫn có
cùng trần post-training/selection; Q3-A không mặc định lấy ngân sách của B/C.

`budget` trả “chưa đo” khi chưa có measurement. Sau này dữ liệu CU từ giao
diện thực và target/time từng workload được nhập để tính
`GPU-hours = targets / observed_targets_per_second / 3600`. A3 có overhead
probe, không dùng tốc độ A1 để tính A3. Không lấy timing forward/backward không
optimizer làm tốc độ train, không hard-code Colab GPU/CU/h hoặc giá mỗi CU.

## Các giới hạn phải giữ rõ

Code đã chuẩn bị không chứng minh model biết viết hoặc giả thuyết đúng.
**Cập nhật 26/11:** người dùng đã cấp quyền Q3-A; bốn kiểm tra engineering
optimizer/JS/memorization/resume đã đạt với fixture hư cấu. Đây là bằng chứng
kỹ thuật, không phải kết quả training khoa học. Naturalistic transfer set,
human labels, hiệu ứng tối thiểu,
preregistration, budget GPU/CU và các kết quả vẫn cần hoàn thành ở đúng giai
đoạn. Draft để trống kết quả và tác giả; không đạt mốc bản thảo có kết quả,
submitted, accepted hoặc published từ việc compile này.
