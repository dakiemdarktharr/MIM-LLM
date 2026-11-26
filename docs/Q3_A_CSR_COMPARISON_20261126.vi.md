# Q3-A: đối thủ CSR và giới hạn claim — 26/11/2026

Một query Undermind bổ sung trả năm candidate records, không phải năm full-text
reviews. Đã kiểm tra riêng nguồn gốc [Counterfactual Sensitivity Regularization
for Trace-Sensitive Reasoning in Large Language Models](https://aclanthology.org/2026.findings-emnlp.539/),
Akter, Shihab và Sharma, Findings EMNLP 2026, tr. 11320–11352. Đã đọc chọn lọc
PDF §3–5.3, bảng 5–6 và scope §4; chưa nhận đọc hết 33 trang hay tái lập kết quả.
DOI do Undermind trả chưa đối chiếu được từ metadata trang chính; dùng URL ACL.

CSR can thiệp reasoning trace, dùng verifier lọc sửa đổi phá tính hợp lệ và
khuyến khích phân phối đáp án thay đổi. Eq. (5) **trừ** KL với nhánh gốc
stop-gradient; không phải tối thiểu hóa JS cho no-op. Bài đã báo counterfactual
correctness, coverage và null-edit preservation, bên cạnh tỷ lệ đổi đáp án;
đổi đáp án tự nó chưa chứng minh đúng. Họ giới hạn áp dụng vào miền có verifier
được kiểm chứng. Đây là công trình đã phản biện, không gắn nhãn preprint.

## Đối chiếu với đúng code của chúng ta

Đây là diễn giải thiết kế của ta, không phải kết quả train post hoặc kết luận
về CSR. `q3a/data.py::ARM_ROLES` và `q3a/runner.py` hiện thực:

| Arm | Supervised CE rows trong chu kỳ bốn hàng | Regularizer |
|---|---|---|
| A0 | base/effective/base/effective | Không |
| A1 | base/effective/base/semantic-noop | Không |
| A2 | base/effective/base/numeric-nuisance | Không |
| A3 | Giống A1 | JS trên train-only state-probe answer spans |

**A1 không dùng JS; A3 không ép toàn bộ prose giống nhau.** Không được mô tả
nhầm hai điều này. Probe huấn luyện là kiểm tra thành phần; inference chính vẫn
phải sinh truyện tự do 3–5 câu, không có bảng trạng thái chuẩn cung cấp cho model.

Không nhận counterfactual training, semantic-preserving edits, hoặc việc đo
đúng/sai bên cạnh invariance là đóng góp đầu tiên. A1−A2 chỉ kiểm tra giá trị
của loại augmentation với nuisance control cụ thể; chưa xác định mọi cơ chế
causal/lexical khác. Khác task hoặc nhỏ hơn về tham số tự nó chưa đủ novelty.

## Cổng trước post-training và viết claim

- Giữ câu hỏi thực nghiệm hẹp: semantic no-op augmentation có giúp giữ đúng
  hệ quả bắt buộc sau nhiều lần cập nhật, vượt numeric nuisance exposure, mà
  không làm giảm khả năng phản ứng với edit thật hoặc viết thành chung chung?
- Không lấy chỉ số gần loss train làm bằng chứng duy nhất. Joint success cần
  giữ/đổi đúng mệnh đề trên cặp truyện và báo writing, coverage, evasion, seed,
  transfer ngoài template cùng uncertainty theo source. Đây là protocol dự kiến.
- Trước khi mở ma trận, đánh giá liệu cần một baseline sensitivity bổ sung.
  Nếu chỉ tái tạo một KL loss/selection rule, gọi là **CSR-inspired component**,
  không gọi là full CSR khi không có editor/verifier/answer space tương ứng.
  Ép đổi đáp án trên semantic no-op sẽ là đối chứng sai ý nghĩa; không làm vậy.
- Nếu chỉ còn một lợi ích trực tiếp từ việc thêm đúng loại ví dụ đã chấm, không
  có principle/failure boundary hay transfer đủ thuyết phục, thu hẹp, gộp hoặc
  dừng manuscript A. Không bảo đảm bài đạt Q3 từ một bảng cải thiện nhỏ.

Calibration2 đang học ngôn ngữ chung; chưa chạy A0/A1/A2/A3 và chưa mở test.
Không thay code training/fingerprints trong lúc warm-up chạy. Các sửa scope
thực sự sau audit cần plan/provenance mới, giữ nguyên mọi run đã xảy ra.

Kiểm tra thêm Appendix I.2–I.3 trong nguồn chính: tác giả đã so sánh các loss
divergence, gồm JS. Vì vậy, đổi KL thành JS cũng không tự tạo novelty cho A3.
Đối chứng bổ sung, nếu triển khai sau feasibility, cần không gian đáp án probe
được xác định và sensitivity chỉ cho cặp effective có đáp án buộc đổi; không
áp loss buộc khác lên toàn bộ đoạn truyện. Đó sẽ là một component adaptation,
không phải tái lập hệ editor/verifier CSR. Chưa thêm arm hay optimizer nào.

Candidate [Written Once, Read Differently: How Language Models' Own Answers
Steer Their Next Ones](https://arxiv.org/abs/2611.03198) mới được xác minh ở mức
metadata/abstract trong lượt này; chưa xem như một full-text audit hoặc bằng
chứng về tính mới của C/Q1. Query và phân loại là targeted search, không phải
systematic review hay bằng chứng “chưa ai làm”.

## Đọc bổ sung trong khi foundation chạy — 26/11

Primary PDF checked additionally at §5.6–5.9, Appendices I/J/K/M (selected
passages and tables, not an assertion of reading all33pages). Table41 includes
ROCStories narrative; Table43 includes prompted narrative/dialogue. Thus “CSR
only studied arithmetic, not stories” would be false. Fine-tuned and prompted
settings must not be conflated. Tables48–50 already compare JS variants.
Listing1 clips negative KL and stops gradients on the original distribution.
Listing4's reward docstring states the reverse KL direction from the displayed
`F.kl_div(p_pert.log(),p_orig)` call. This is a documentation/code discrepancy,
not evidence that the published experiments used either implementation.
No author repository or reproduction was verified here. Source: [PDF](https://aclanthology.org/2026.findings-emnlp.539.pdf).

KL direction above follows the [official PyTorch definition](https://docs.pytorch.org/docs/2.15/generated/torch.nn.KLDivLoss.html):
`F.kl_div(log(q),p,batchmean)` computes `KL(p||q)`. A local read-only numeric
check with p=(.8,.2),q=(.3,.7) returned0.5341108087103077, matching that direction;
the reverse is0.5826853020432394. This checks the formula, not the authors' runs.

Correction to the earlier DOI uncertainty: [current ACL metadata](https://aclanthology.org/2026.findings-emnlp.539/)
now explicitly lists `10.18653/2026.findings-emnlp.539`. This does not establish
that a differently formatted DOI from an aggregator resolves.

Diễn giải cho thiết kế của ta: hai truyện base/effective đều mô tả thế giới hợp
lệ; chúng không phải trace đúng và trace bị phá. Vì thế không thể sao chép
verifier gate “valid original/invalid edited trace” rồi gọi là so sánh CSR đầy
đủ. Nếu thêm sensitivity baseline, phải ghi rõ **component adaptation**, answer
space nào được chiếu, gold fact nào buộc đổi, dấu loss/stop-gradient/clipping,
target/input/probe accounting và nguồn lực. Không ép toàn prose khác nhau hoặc
dùng xác suất đổi nhãn thay tính đúng. Chưa thêm arm hay train post nào.

Q3-A chỉ còn giả thuyết đóng góp thực nghiệm có điều kiện: so variation liên
quan nhưng giữ hệ quả với numeric nuisance đã khớp, tìm failure boundary và
transfer có kiểm chứng trên đoạn văn tự do. Khác dataset/backbone/quy mô hoặc
thêm JS tự nó chưa đủ. Trước post cần chốt baseline/protocol sau writing gate;
nếu chỉ đạt template exposure benefit thì gộp/dừng theo stop rule. Không sửa
learning code/fingerprints c18 hoặc dữ liệu của foundation đang chạy.
