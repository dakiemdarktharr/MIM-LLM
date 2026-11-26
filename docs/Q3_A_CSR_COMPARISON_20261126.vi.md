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

Candidate [Written Once, Read Differently: How Language Models' Own Answers
Steer Their Next Ones](https://arxiv.org/abs/2611.03198) mới được xác minh ở mức
metadata/abstract trong lượt này; chưa xem như một full-text audit hoặc bằng
chứng về tính mới của C/Q1. Query và phân loại là targeted search, không phải
systematic review hay bằng chứng “chưa ai làm”.
