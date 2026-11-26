# Q3-A — phạm vi quy tắc đã kiểm trên train, 27/11/2026

Đây là kiểm tra dữ liệu và oracle toán học, **không phải kết quả của model**.
Script `scripts/audit_q3a_rule_support.py` đọc manifest có chữ ký và đúng
6.000 nhóm train của dataset
`623091c0178df3208605757222b20ed18d17fc3f4576b3f63edeb53f4b61094d`.
Train SHA256: `bb2fd3c8568ebb75c3c7fe1ae431a05ce0e6babb657db04db177d183886bc573`.
Nó kiểm hash generator, số nhóm, split và contract của từng bundle trước khi đếm.

## Đã đo trên train

| Trạng thái tại hạn | Base | Effective | No-op | Numeric nuisance (`surface`) |
|---|---:|---:|---:|---:|
| Chưa có điện, có quyền | 2.000 | 2.000 | 2.000 | 2.000 |
| Có điện, chưa có quyền | 2.000 | 0 | 2.000 | 2.000 |
| Có điện, có quyền | 2.000 | 4.000 | 2.000 | 2.000 |
| Chưa có điện, chưa có quyền | 0 | 0 | 0 | 0 |
| Điện về đúng hạn | 0 | 0 | 0 | 0 |

Đây là bốn biến thể phụ thuộc trong cùng một nhóm, không phải 24.000 truyện
độc lập. Mỗi độ sâu 1–6 có 1.000 nhóm. No-op hiện hành giữ cả năm fact được
theo dõi. Vì thiếu ca đúng hạn và hai blocker đồng thời, không suy ra model
biết mọi phép hội điều kiện hoặc mọi dạng chỉnh sửa giữ nguyên hệ quả.

## Ví dụ phát triển và phép kiểm thành phần

Đặt hạn là 9:00, giả định mọi lần chuyển chìa đã hoàn tất và không còn thay đổi
đến lúc ra quyết định. Oracle hiện hành định nghĩa

\[
P=[t_{\mathrm{power}}\leq t_{\mathrm{deadline}}],\qquad
\mathrm{open}=P\land R,
\]

với `R` là có quyền mở. Bảng sáu trường hợp được dựng từ thời điểm trước,
đúng và sau hạn một phút, kết hợp hai giá trị `R`. Cả sáu khớp oracle. Đây là
ca toán học do chúng ta tạo, không phải model trả lời đúng sáu bài.

Nếu đồng thời thiếu điện và thiếu quyền, mỗi điều kiện thiếu riêng lẻ đã đủ
giải thích việc chờ; nêu cả hai cũng đúng. Sau khi chỉ đổi điện từ 9:05 thành
8:55 trong lúc vẫn thiếu quyền, hành động vẫn là chờ và tủ vẫn khóa, nhưng
mệnh đề “đã có điện” phải đổi. Do đó **hệ quả không đổi không có nghĩa mọi
mệnh đề hoặc mọi lý do đều bất biến**. Không được ép model tiếp tục nói mất
điện ở bản đã có điện.

Script đưa cặp phát triển này vào encoder probe thật, dùng tokenizer đóng
băng và context của c18: holder/action/cabinet/permission nhận cùng target;
probe `power_available` từ chối target bị đổi, đúng với contract. Cặp này
không hợp lệ như một full-state no-op của dataset hiện tại; không bypass
validator hoặc thêm nó vào train/test. Mọi rubric mở rộng cần chấp nhận các
lý do đủ hợp lệ, đồng thời bắt các fact đã đổi phải được chấm theo bản mới.

Với sự kiện đồng thời, cách hiểu ngôn ngữ phải nêu thứ tự rõ. Quy tắc `<` có
thể biểu diễn việc điện trở lại sau quyết định cùng phút; đây chỉ là ví dụ
thiết kế khác, chưa triển khai hoặc đưa vào benchmark. Không đổi `<=` sau
khi quan sát output, không gộp hai ngữ nghĩa thành cùng một nhãn.

## Tái lập và phạm vi bằng chứng

```powershell
.venv/Scripts/python.exe scripts/audit_q3a_rule_support.py --dataset data/processed/q3a-launch-20261126/a --foundation-plan configs/q3a/foundation_plan.json --output <new-audit.json>
```

Receipt public: `configs/q3a/rule_support_audit_20261127.json`, SHA256
`2d4c2543a29e74edcf3ac8cc1660d3b4abc9852d5ab9c8bd261c17e6de4311d3`.
Script SHA256: `00b7416440da4e6af6f0fe20e1e8d211d22ef44fa01a06565463fc8b563e9883`.
Lệnh trên dữ liệu thật và Ruff check/format đã đạt. Output phải là đường dẫn
mới để giữ các audit cũ. Không chạy optimizer, tải model hoặc sinh văn bản;
không fit tokenizer và không thu nhãn người.

Không tải/parse dòng validation hoặc test của controlled dataset. `load_plan`
vẫn kiểm hash đầy đủ các input foundation đã encode, bao gồm file validation;
không decode/scoring validation trong audit này. Metadata này sửa cách mô tả
quá rộng `validation_test_content_read=false` ở receipt đầu, được giữ local
trong artifacts cùng receipt trước khi thêm guard generator/output. Các số
đếm và kết quả probe không đổi. Không tắt integrity checks để tránh hash.

Quyết định hiện hành: công bố đúng support hữu hạn và giữ test khóa. Muốn
claim rộng hơn cần version/challenge/rubric/analysis prospectively được chốt
trước đánh giá model; audit không đăng ký challenge đó, không thay 24-run
matrix, không tạo kết quả test hoặc giảm rủi ro novelty bằng một bảng chân trị.
