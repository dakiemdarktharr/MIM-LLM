> **Scope/authorization update, 26 November 2026:** Q3-A now uses numeric irrelevant-clock edits as A2, replacing the historical punctuation control. Q3-A bounded Colab training is authorized; B/C/Q1 and tokenizer fitting remain closed. Current plan ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142. See [scope review](SCOPE_REVIEW_BEFORE_TRAIN_20261126.vi.md). Earlier zero-training receipts below describe their original preparation session.

# Kiểm chứng bàn giao A/B/C — 26/11/2026

Đây là kiểm chứng **chuẩn bị trước train**, không phải kết quả nghiên cứu.
Không optimizer update, fit tokenizer, human labels hay paid Colab runtime.
Policy production giữ false/false và hai danh sách authorized IDs rỗng.

## Phạm vi mã đã có

- A: can thiệp effective/no-op, punctuation control khớp byte/edit, CE và probe-JS,
  checkpoint/resume, generation, blind packet, phân tích paired và bảng LaTeX.
- B: event CE + delayed QA trên disposable prefix, lag/write controls, target
  budget chính xác, continuation và probe panels, human-label analysis/bảng.
- C: collector từ checkpoint warm-up thật, token-wise grammar sampling,
  provenance/surprisal matching/sealing/binding, suffix CE theo actual event,
  free/fixed two-stage generation giữ raw IDs, coverage/evasion và human analysis.
- C grammar train dùng known-holder scaffolding. Không diễn giải chín chuỗi
  hợp lệ thành free authorship, on-policy learning hay novelty đã chứng minh.
- PPL validation/test của cả ba dùng corpus TinyStories gốc, không lấy dòng
  format dẫn xuất. Test yêu cầu frozen selection/registration/checkpoint hashes.

## Đã thực hiện và kết quả thực

| Kiểm tra | Kết quả |
|---|---|
| `python -m pytest -q` trong `.venv` | **131 passed, 10 deselected** |
| Ruff trên src/tests và các script chuẩn bị | Pass |
| CPU/CUDA preflight A/B/C | Pass; tham số giữ nguyên; zero optimizer steps |
| Dense CE graph `[2,2048,259]` trên hai backbone, CPU/CUDA | Loss/gradient hữu hạn, tham số giữ nguyên |
| Hai notebook, mỗi notebook bốn code cells | Chạy local bằng nbclient, zero errors/optimizer steps; source không lưu outputs |
| `python scripts/build_papers.py` | Cả bốn Pass; không undefined citations/references hoặc overfull/underfull boxes |
| Render và xem A/B/C | **5/4/5 trang**, đã xem toàn bộ 14 trang; không lỗi glyph, bảng tràn/cắt |

Mười test bị giữ lại gồm original fitting/training và optimizer/JS/resume của
pipeline mới. Không được mô tả chúng là đã pass. Chúng chỉ chạy sau lệnh train
mới và permission hợp lệ. Tính đúng optimizer/resume thực tế và memorization
tiny batch còn phải kiểm chứng khi đó.

Máy kiểm tra: Windows, Python 3.11.9, PyTorch 2.10.0+cu128, **RTX 5050 Laptop**
(nvidia-smi báo 8.151 MiB). minGRU: **2.099.864** tham số; Transformer:
**2.119.408**. Dense-CE CUDA peak allocated lần lượt 634.588.160 và 788.743.680
bytes. Đây không gồm optimizer state hay graph phụ A3 và **không phải** throughput,
VRAM full train hoặc GPU-giờ. Colab GPU/CU/chi phí chưa đo.

## Plans và dữ liệu hiện hành

Registry local `artifacts/three-q3-final-20261126/registry.json`; data dưới
`data/processed/three-q3-final-reviewed`. Snapshot công khai ở
`configs/q3{a,b,c}/prepared_snapshot.json`.

| Bài | Plan ID | Max prompt + generation reserve |
|---|---|---|
| A | `77e05540bdef194a755c10219e6c9a1858d4b9b0e124a81c02ab834ef409283a` | 1.664 tokens |
| B | `3d1397207e4b494e805d78647c35b8dfa97047e5170eb994299c2f73b4018ed2` | 1.728 tokens |
| C base, bank pending | `0f5397e0264be1e270ec4b78c88a8e6a851701d1b9bad62b7598ec5185037b0d` | 1.241 tokens |

A/B: 6.000/400/400 sources mỗi bài. C:600/60/120 prompts, **chưa có** production
model-history bank. Shared warm-up có 3.000/300/300 underlying source groups,
thêm 2.792/277/280 same-split format rows. Tổng dòng5.792/577/580 không phải số
truyện độc lập. Source hashes và original corpus pin nằm trong manifests.
Xem [dataset notice](../DATA_NOTICES.md).

Sáu warm-up jobs +72 post jobs chỉ là DAG, chưa chạy. Mỗi bài48M post targets
và7,2M reserve; sharedwarmup30M tính một lần. Tổng full-reserve195,6M targets.
Equal targets không bảo đảm equal compute; B replay và C collection/NLL đều
phải log. Không được suy thời gian hoặc CU từ các kiểm tra forward/backward.

## Các sửa lỗi và giới hạn quyết định

1. A2 được gọi đúng punctuation/surface control; không nhận là full paraphrase.
   Khớp byte length và số ký tự sửa, nhưng khác vị trí/loại ký tự. A đóng timeline
   tới decision để tránh tự thêm sự kiện quá khứ làm vô hiệu mandatory facts.
2. B0 counterbalance window selection độc lập window order. Mỗi counted write
   thật sự thay đổi vị trí. Prose prompt cắt đúng probe_end của high window;
   không dùng target revision ở phía sau để gán nhãn lag/write sai.
3. C metadata origin không vào learner: estimand là input-distribution coupling
   trên matched support. Bank frozen từ initialization không phải on-policy.
   Không có genuine checkpoint thì chặn, không dùng teacher fixture thay C1/C2.
4. C self/peer phải khớp source/place, lengthgap≤32byte và NLLgap≤0,25nats/byte;
   min30 sources/learner và có nonidentical histories. Default24 feasibility
   sources không đủ điều kiện bank full. Không nới caliper để săn gain.
5. C main eval không mask, giữ nguyên raw first IDs, kể cả invalidUTF8/no-event;
   strict success không credit lỗi đó. Kiểm tra prefix validity, format, coverage
   và follow-up để không thưởng cách né sự kiện.
6. B/C blank labels bị từ chối; hai reader thật chấm độc lập, adjudication trước
   primary effect. Bootstrap giữ source clusters và mọi observed seed; show seed
   variability riêng. Testsource hash không thay cho selection lock thực tế.
7. Shared format warm-up giữ nguyên source groups/splits và5M cap; original
   PPL loại derived rows. Không suy instruction capability từ việc đã tạo data.
8. LaTeX đã sửa undefined cite key và overflow trong common methods. Tác giả và
   kết quả chưa điền; generated PDFs local, ignored, không đưa GitHub.

## Việc còn cần lệnh train mới hoặc bằng chứng bên ngoài

Bounded optimizer/overfit/resume checks → writing feasibility → GPU/CU calibration
và resource cap → shared warm-up → C genuine bank/overlap gate → balanced post
runs → validation selection → frozen test → real readers/analysis. A/B có thể
post khi parent phù hợp hoàn tất; C không thể bỏ qua bank dependency.

Nguồn tự nhiên có giấy phép, transfer ngoài templates/support nhỏ, độ tin cậy
người chấm và incremental novelty vẫn là scientific gates. Không có bảo đảm
“không còn lỗi”, chất lượng chat, Q3 hoặc acceptance. Nếu template-only, quality
confound, thiếu overlap hoặc đóng góp trùng prior work thì sửa/gộp/dừng.
Mục tiêu chat MIM-LLM không được coi hoàn tất bởi ba pilot component này.

Xem [runbook](THREE_Q3_PRETRAIN_RUNBOOK.vi.md) và brief/10 câu trả lời cho từng
bài: [A](Q3_A_BRIEF_AND_ADVISOR_QA.vi.md), [B](Q3_B_BRIEF_AND_ADVISOR_QA.vi.md),
[C](Q3_C_BRIEF_AND_ADVISOR_QA.vi.md). Hash bundle/round-trip checks lưu local
trong cùng thư mục artifact; không đưa ZIP, datasets, weights hay private vault
vào Git. Không có result-bearing draft/submission/acceptance/publication mới.
