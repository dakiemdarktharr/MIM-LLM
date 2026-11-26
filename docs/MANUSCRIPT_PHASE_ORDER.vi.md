# Chỉ compile sau khi có kết quả — chỉ dẫn 26/11/2026

Người dùng yêu cầu hoàn tất các pha train, thu thập dữ liệu, đánh giá/test và
phân tích kết quả thật rồi mới compile LaTeX. Áp dụng **theo từng bài độc lập**;
không yêu cầu chờ cả bốn bài cùng hoàn tất. Đây là thứ tự làm việc, không phải
một bước xin phép biên dịch mới. Chỉ dẫn này thay hướng dẫn build ở pha chuẩn
bị trong các runbook cũ. Có thể chỉnh source khi cần, nhưng chưa chạy TeX.

## Hiện tại

Q3-A chưa có training/metrics/checkpoint khoa học trên Drive được xác minh;
chưa thu nhãn người thật hoặc có kết quả test. B/C/Q1 cũng chưa đủ điều kiện.
**Cả bốn bài đang khóa compile.** Không dùng unit fixtures, planning draft,
source manifest hay ô checkbox để nhận đã hoàn tất các pha khoa học.

Trước chỉ dẫn này, đã dựng generic drafts và một bản layout J.UCS V5 sáu trang.
Các PDF/log đó được giữ local như lịch sử, không là bản thảo có kết quả hoặc
bằng chứng hoàn tất nghiên cứu. Không tiếp tục dựng để sửa hình thức ở giai đoạn
này. Code/header hiện hành sau chỉ dẫn chưa được compile lại theo đúng thứ tự.

## Khóa trong code

`scripts/build_papers.py` và `scripts/build_q3a_jucs.py` kiểm tra
`mim_llm.manuscript_workflow.require_results_before_build` **trước khi tìm hoặc
gọi compiler**. Không có tùy chọn bỏ qua cho việc dựng draft sớm.

Sau khi các pha khoa học thật sự hoàn tất, lưu receipt local:
`artifacts/manuscript-readiness/<paper>.json`, với `<paper>` là `q3-a`, `q3-b`,
`q3-c` hoặc `q1`. Receipt phải ghi đúng bài, `scientific_results_available=true`,
và cả bốn pha `data_collection`, `training`, `evaluation`, `analysis`; mỗi pha
có `status=complete`, cùng danh sách `evidence` gồm `path` và `sha256` của các
artifact thật đã kiểm tra. Dùng manifest/genuine run summaries, metrics,
generation/annotation records và kết quả thống kê tương ứng; không dùng dữ liệu
hư cấu của test làm receipt nghiên cứu. Giữ raw data/labels/checkpoints private
hoặc local/Drive theo policy, không đưa chúng lên Git chỉ để build.

Guard xác minh receipt, sự tồn tại và SHA của các file. **SHA chứng minh danh
tính file, không tự chứng minh nội dung đúng hoặc nghiên cứu đã hoàn tất.**
Agent/người nghiên cứu vẫn phải đối chiếu plan/run/seed, full budgets, khóa test,
nhãn người thật, kết quả âm, uncertainty và các gate của bài trước khi tạo
receipt. Kết quả âm vẫn là kết quả thật; không yêu cầu hiệu ứng thuận chiều.

Khi đủ điều kiện, có thể dựng riêng một bài bằng
`python scripts/build_papers.py --paper q3-a`; không tự mở build B/C/Q1. Bản
J.UCS dùng `python scripts/build_q3a_jucs.py --template-zip OFFICIAL_V5_ZIP`.
Lúc đó phải cập nhật abstract/results/discussion từ bằng chứng thật, rồi mới
biên dịch và visual QA. Không xem compile thành công là chứng nhận chất lượng Q3
hoặc quyết định nhận bài.

## Trọng tâm tiếp theo

Hoàn tất quyền Drive → kiểm chứng lưu/đọc lại → engineering checks của notebook
→ warm-up giới hạn và đo tài nguyên → writing feasibility → matrix đã khai báo
→ thu/chấm output và phân tích → viết theo kết quả → compile/visual QA.
Không giả định được phép train lại sau khi nhìn test; mọi vòng train bổ sung
phải giữ test lock và ngân sách, công khai amendment nếu cần.
