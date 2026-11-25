# Q3-A — Sổ nguồn và phạm vi kiểm chứng

Ngày truy xuất/đọc: **25/11/2026**, Asia/Ho_Chi_Minh. Mục đích là chuẩn bị đề cương
Q3-A; không phải systematic review có protocol tìm kiếm toàn diện.

## Phương thức và giới hạn

- Đối chiếu trang chính thức, metadata, PDF và các phần liên quan. Có **17 PDF**
  tải thành công; 16 bài trong tạp chí/kỷ yếu phản biện và 1 preprint. Đây là số
  nguồn trong tập đọc, không phải số công trình trùng đã xác minh trong toàn ngành.
- Đọc sâu có chọn lọc theo nhiệm vụ/metric/validity. Không tuyên bố đọc từng dòng
  hay chạy lại mã tác giả. Chưa xác minh giấy phép của mọi dataset trong các bài.
- Có sàng lọc abstract của 3 nguồn bổ sung bên dưới; chúng không được tính vào 17
  PDF. Repo/model/dataset cards phục vụ thiết kế không được tính thành paper.
- Lượt Undermind mới bị hạn mức miễn phí chặn trước khi khởi chạy; tool báo reset
  14:00 UTC, 21:00 giờ Việt Nam ngày 25/11. Không có kết quả mới từ lượt đó.
- Khảo sát trực tiếp dùng web search, ACL Anthology, arXiv và nguồn tác giả; không
  tuyên bố đã quét đầy đủ OpenReview/PMLR/Crossref/OpenAlex hoặc kho Việt Nam trong
  lượt này. Những nội dung được khảo sát trước có sổ riêng ở `docs/RESEARCH.md`.

Các truy vấn bổ sung chạy và lưu ở cuối lượt:

1. `site:aclanthology.org narrative counterfactual invariance temporal entity tracking generation benchmark`
2. `site:arxiv.org story continuation state consistency overwrite temporal counterfactual benchmark 2026`
3. `site:aclanthology.org "state" "counterfactual" "generation" "2026"`

Ngoài truy vấn này, đã mở trực tiếp các nguồn theo title/URL của tài liệu nền và
theo references/related-work của bài đọc. Một kết quả search có từ khóa liên quan
chỉ là ứng viên; phân loại cuối dựa trên task/metric trong nguồn chính.

## Tập PDF đã truy xuất

| Key | Nguồn chính / tình trạng | Phần đọc được dùng cho phân tích |
|---|---|---|
| timetravel | [Counterfactual Story Reasoning and Generation — EMNLP-IJCNLP 2019](https://aclanthology.org/D19-1509/) | Task, causal invariance, dữ liệu, human/automatic evaluation §5 và limitations. |
| cip | [Social Commonsense Reasoning with Multi-Head Knowledge Attention — Findings EMNLP 2020](https://aclanthology.org/2020.findings-emnlp.267/) | Introduction, task CIP §2, nguồn/cân bằng dữ liệu, setup và bảng kết quả CIP. |
| pasta | [PASTA: A Dataset for Modeling PArticipant STAtes in Narratives — TACL 2023](https://aclanthology.org/2023.tacl-1.73/) | Task/state perturbation; §6.2 logical/inferable/ALL và §6.5 agreement. |
| entity2023 | [Entity Tracking in Language Models — ACL 2023](https://aclanthology.org/2023.acl-long.213/) | Task, chuỗi cập nhật, đánh giá trạng thái cuối, setup và phạm vi generalization. |
| naturaltracking | [Entity tracking emerges in sub-billion parameter language models and exceeds human performance in naturalistic narratives — EMNLP 2026](https://aclanthology.org/2026.emnlp-main.2231/) | §3 task, template generation, recency; appendix explicit one-word và implicit probability task. Không suy ra ưu thế với mọi kiểu truyện/người. |
| facttrack | [FactTrack: Time-Aware World State Tracking in Story Outlines — NAACL 2025](https://aclanthology.org/2025.naacl-long.144/) | Pipeline atomic facts/validity intervals và đối tượng evaluation là outline. |
| constory | [Lost in Stories: Consistency Bugs in Long Story Generation by LLMs — Findings ACL 2026](https://aclanthology.org/2026.findings-acl.410/) | Benchmark, taxonomy, checker; Appendix A.2 dữ liệu lỗi chủ đích và human comparison. Không dùng kết quả gieo lỗi làm chứng cứ đủ cho lỗi tự nhiên. |
| conwriter | [ConWriter: Transition-Constrained Stateful Long-Form Story Generation with Lightweight Neuro-Symbolic Consistency Control — Findings EMNLP 2026](https://aclanthology.org/2026.findings-emnlp.359/) | Abstract/introduction, external memory/state/repair và evaluation scope. Không tái lập pipeline. |
| temporalscope | [Evaluating Temporal Consistency in Multi-Turn Language Models — ACL 2026](https://aclanthology.org/2026.acl-long.2133/) | Introduction, ChronoScope task/chain types, dữ liệu Wikidata và temporal scope stability. Không đồng nhất với free story continuation. |
| scratchworld | [ScratchWorld: Evaluating If World Models Compute Executable Consequences — arXiv:2606.31689v2, 28/10/2026, preprint](https://arxiv.org/abs/2606.31689v2) | Execution-grounded task, changed-field metric, no-change baseline, counterfactual changed/invariant diagnostics. Chưa xác nhận venue phản biện. |
| causal2024 | [A Causal Approach for Counterfactual Reasoning in Narratives — ACL 2024](https://aclanthology.org/2024.acl-long.354/) | Abstract/introduction/formal task; VAE/classifier/commonsense và cảnh báo dataset-specific artifacts. Chưa audit toàn bộ kết quả. |
| trip | [Tiered Reasoning for Intuitive Physics: Toward Verifiable Commonsense Language Understanding — Findings EMNLP 2021](https://aclanthology.org/2021.findings-emnlp.422/) | Task plausibility/conflicting sentence pair/underlying states; không phải đầu ra tiếp nối truyện. |
| propara | [Tracking State Changes in Procedural Text: a Challenge Dataset and Models for Process Paragraph Comprehension — NAACL 2018](https://aclanthology.org/N18-1144/) | Task và state existence/location trong process text, giới hạn chuyển sang narrative. |
| openmeva | [OpenMEVA: A Benchmark for Evaluating Open-ended Story Generation Metrics — ACL 2021](https://aclanthology.org/2021.acl-long.500/) | Metric validation, perturbation và human correlation; không ngoại suy kết quả lịch sử thành kết luận về mọi judge hiện nay. |
| checklist | [Beyond Accuracy: Behavioral Testing of NLP Models with CheckList — ACL 2020](https://aclanthology.org/2020.acl-main.442/) | Minimum functionality, invariance và directional expectations. |
| agreement | [Inter-Coder Agreement for Computational Linguistics — Computational Linguistics 2008](https://aclanthology.org/J08-4004/) | Reliability/validity, chance agreement, prevalence và lựa chọn hệ số; tài liệu dài 42 trang, đọc phần phục vụ protocol. |
| stats | [The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing — ACL 2018](https://aclanthology.org/P18-1128/) | Đơn vị mẫu, assumptions và chọn kiểm định; clustered paired-source bootstrap của Q3-A là thiết kế cụ thể đề xuất, không gán nguyên xi cho bài hướng dẫn. |

Tên/ID và hash đầy đủ nằm trong [manifest truy xuất](Q3_A_SOURCES.json). PDF và
text extraction lưu cục bộ ở `artifacts/q3-a-research-20261125`, bị Git ignore;
manifest không phân phối lại toàn văn. Hash xác định đúng bản đã tải, không tự
chứng minh chất lượng phương pháp hay giấy phép tái phân phối dataset.

## Nguồn sàng lọc thêm và các nghĩa dễ nhầm

| Nguồn | Mức đọc / lý do phân loại |
|---|---|
| [CEval — INLG 2024](https://aclanthology.org/2024.inlg-main.6/) | Metadata/abstract. Counterfactual text editing đổi nhãn classifier; không đồng nhất với diễn tiến thế giới truyện. |
| [Respecting Temporal-Causal Consistency: Entity-Event Knowledge Graph for Retrieval-Augmented Generation — EACL 2026](https://aclanthology.org/2026.eacl-long.90/) | Metadata/abstract. ChronoQA/E2RAG: narrative QA với retrieval/graph ngoài. |
| [TRACE — Findings EMNLP 2026](https://aclanthology.org/2026.findings-emnlp.1045/) | Metadata/abstract. Sequential temporal knowledge editing; khác memory ẩn dùng để viết tiếp. |
| [TinyStories dataset card](https://huggingface.co/datasets/roneneldan/TinyStories) | Data/language/license metadata. Trang hiện ghi CDLA-Sharing-1.0. Chưa tải corpus trong lượt này. |
| [SmolLM2-135M-Instruct model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) | Nguồn tác giả để xét capability reference; chưa chạy hay đo chất lượng trên Q3-A. |

Không đếm trùng arXiv và phiên bản hội nghị thành hai công trình. Không đánh đồng
Counterfactual Invariance Prediction trong truyện với những bài khác chỉ cùng
viết tắt CIP. Cũng không dùng số lượng kết quả tìm kiếm làm bằng chứng tính mới.

## Bằng chứng nội bộ và tính tái lập

- Rà source trên base commit `68e8344afeca39f339b30c404b4618bca12e9c0c`:
  `src/mim_llm/benchmark.py`, `oracle.py`, `evaluation.py`.
- Dùng `rg` để định vị thiết kế pair, sampling không lặp, nghĩa vụ và bootstrap;
  đọc đoạn mã trước khi đưa ra nhận xét. Không sửa code trong lượt lập hồ sơ.
- PDF lấy từ trang bài chính thức, text extraction bằng PyMuPDF; nguồn đầu tiên
  của TRIP bị timeout ở URL v2, sau đó tải thành công URL mặc định. Không che việc
  tải lỗi trong quá trình tìm; manifest chỉ ghi các file thành công cuối cùng.
- Mọi đề xuất extension, mức sample size, ngân sách và lời đáp giảng viên ở các
  file liên quan đều là planning, không phải quan sát người/model mới.
