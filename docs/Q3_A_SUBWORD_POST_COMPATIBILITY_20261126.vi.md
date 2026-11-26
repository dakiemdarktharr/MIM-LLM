# Q3-A — kiểm tương thích post-training với tokenizer subword

26/11/2026. Đây là **chuẩn bị thành phần**, chưa có post-training plan được mở,
chưa train A0–A3 hoặc mở test. Đặt package mới tại `mim_llm.q3a_subword`, giữ
nguyên toàn bộ source fingerprints của các plan byte cũ và foundation đang học.

CE dùng target response-only dịch1token và mask theo độ dài của foundation.
Chỉ chiếu LM head ở vị trí có nhãn. Probe JS A3 chỉ là câu hỏi thành phần lúc
train, không thay yêu cầu output chính3–5câu truyện và không cho bảng trạng thái
chuẩn vào inference. Không nhận JS/null-edit augmentation là novelty mới.

Header probe byte cũ kết thúc `Answer: ` có thể bị BPE gộp khoảng trắng với từ
đầu đáp án. Biến thể subword dùng `Answer:\n`, kiểm encode từng phần khớp encode
nguyên chuỗi, so JS trên cùng answer+EOS; không âm thầm nhận boundary không ổn
định. Sửa đổi này phải có trong post-plan/provenance mới, không sửa input của
run cũ. Code không tự chuyển hoặc resume plan byte sang tokenizer mới.

Bốn kiểm tra không optimizer đạt: shifted CE/budget/EOS/context, fail-closed
boundary, JS loss/gradient selected-head khớp tham chiếu dense cho cả2backbones,
và stable targets cho5loại probe. Chúng không là scientific quality scores.

Audit dữ liệu thật **train only**:

| Mục | Số đã kiểm |
|---|---:|
| Source bundles | 6.000 |
| CE story rows qua4roles | 24.000 |
| Invariant component probe pairs qua5keys | 30.000 |
| Probe rows | 60.000 |
| Input tokens lớn nhất của toàn bộ các hàng trên | 305 / context1.024 |

Mọi boundary/target alignment/EOS đã qua assert. Audit không tạo model, không
optimizer/tokenizer update, không đọc validation/test và không đo performance.
Input SHA`bb2fd3c8568ebb75c3c7fe1ae431a05ce0e6babb657db04db177d183886bc573`;
script/objective normalized source hashes cùng tokenizer snapshot trong
`configs/q3a/subword_post_compatibility_receipt.json`. Không xem pass là bằng
chứng nuisance tương đương mọi mặt hoặc cải thiện causal reasoning.

Primary subword runner/plan, generation, scoring, resource matching và registered
analysis vẫn phải được hoàn tất/kiểm riêng sau khi writing feasibility đủ căn
cứ; các helper này chưa phải pipeline post-training hoàn chỉnh. Foundation
scientific plan `c18fcecd62ad…` vẫn load/verify nguyên vẹn sau khi thêm package.

## Tình trạng tài nguyên và xác thực hiện tại

Sau lượt foundation1, phiên xin GPU mới có thông báo “No backend with GPU
available”; phiên được cấp sau đó là CPU, rate UI0,08CU/h. Không dùng CPU thay
cho CUDA profile hoặc train. Phiên CPU0updates đã được terminate; UI xác nhận
0active sessions/rate0/balance596,66. Không thêm driver reservation; vẫn1/8.

Google yêu cầu xác minh danh tính chủ tài khoản trong flow mount mới. Đây là
bước người dùng thực hiện, không phải bằng chứng quyền Drive cũ bị thiếu. V3
bootstrap/profiler đã soạn trong notebook; tệp overlay V3 chưa upload/thực thi
trên VM và CUDA profile chưa chạy. Tiếp tục sau xác minh và GPU availability;
không tự mở optimizer/test/LaTeX trong lúc chờ. Goal vẫn active, chưa complete.
