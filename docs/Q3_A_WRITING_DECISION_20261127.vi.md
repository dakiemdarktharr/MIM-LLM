# Tổng hợp phiếu feasibility — 27/11/2026

Đây là công cụ chuẩn bị trước khi sinh panel subword, không phải đánh giá đã
thu thập. Hiện chưa có output panel mới hoặc nhãn người thật. Quy tắc đã chốt
trước đó trong `configs/q3a/foundation_writing_rule.json`, SHA256
`590471e3dc722b083e95473c6b3648b18aab7abf0c5746ad1e5d6358d4da7910`,
được giữ nguyên; công cụ không hạ ngưỡng để đạt pass.

`scripts/score_q3a_foundation_writing.py` đọc panel đầy đủ, manifest, packet đã
ẩn model ID, private key và CSV do người đọc thực sự điền. Nó đối chiếu từng
prompt/continuation/mapping với output nguồn và kiểm hash trước khi tổng hợp.
Phiếu trống, thiếu dòng hoặc chưa điền hết trường cho kết luận **pending**,
không tự suy ra nhãn. ID lạ/trùng, số ngoài miền, thời gian âm/NaN/inf, nhiều
rater hoàn chỉnh hoặc thay rule bị từ chối; không âm thầm loại dòng lỗi.

Chỉ sau đủ 34 phiếu, từng backbone phải có ít nhất12/16 đoạn có điều kiện
đồng thời đạt format, fluency>=3, theo prefix, có sự kiện mới, nhất quán và
không mơ hồ; đoạn vô điều kiện cũng phải đạt. Với yêu cầu vô điều kiện, người
đọc phải đánh `follows_prefix=0` nếu không tuân thủ yêu cầu đúng3câu. Công cụ
không dùng đếm dấu chấm để giả lập đánh giá của con người. Nhóm đoạn có điều
kiện giống nhau sau NFKC/casefold/gộp khoảng trắng không được quá4. Quy tắc75%
là sàng lọc kỹ thuật có tính mô tả, không phải ngưỡng đã được kiểm định.

Ví dụ lệnh cho **sau khi có dữ liệu thật** (các đường dẫn output cần mới,
giữ panel/private key/CSV trong artifacts hoặc Drive):

```powershell
.venv\Scripts\python.exe scripts/score_q3a_foundation_writing.py --review-directory <real-panel> --manifest <frozen-manifest> --packet-directory <real-packet> --labels <genuine-completed-CSV> --rule configs/q3a/foundation_writing_rule.json --output <new-private-summary.json>
```

Báo cáo ghi hash CSV, packet, key, samples, rule và source. Trạng thái pass
không mở khóa train post tự động. Chỉ một tác giả chấm vẫn không phải xác nhận
độc lập hoặc độ đồng thuận giữa hai người; phần mềm không xác thực được một
người đã thật sự đọc, nên provenance người thật còn cần bằng chứng riêng.

Kiểm tra:14tests đạt (`test_writing_decision.py`, `test_writing_packet.py`),
gồm10tests mới về thiếu nhãn, NaN, đổi key/rule, ngưỡng riêng cho hai model,
và lặp output dù có nhãn dương. Tất cả fixture nằm trong thư mục tạm và được
ghi rõ giả lập; chúng không phải scientific observations. Ruff đạt. Không có
optimizer, tokenizer fit, test release hoặc compiler. Không sửa source thuộc
fingerprint c18; post plan tương lai phải dùng snapshot source cuối mới.
