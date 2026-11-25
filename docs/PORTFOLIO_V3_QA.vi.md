# Kiểm tra revision 3 — hoàn tất 26/11/2026

Thiết kế và tra nguồn ngày 25/11; tiếp tục kiểm tra và ghi nhật ký sang ngày
26/11, múi giờ Asia/Saigon. Đây là kiểm tra tài liệu/planning metadata, không
phải chứng nhận các phương pháp mới đã triển khai hoặc sẵn sàng train.

- Bốn LaTeX build thành công bằng `python scripts/build_papers.py`: mỗi bài
  **4 trang**, tổng **16 trang**. Không lỗi biên dịch, undefined references,
  overfull/underfull box hoặc warning trong report/log được kiểm tra. Đặt
  `FONTCONFIG_FILE` theo fonts.conf của runtime cho phiên build này.
- Render và xem cả 16 trang: tiêu đề, bảng, công thức, references và số trang
  nằm trong lề, không chồng chữ hoặc bị cắt. Đây là bố cục article để nghiên
  cứu; chưa kiểm tra theo template/giới hạn trang của một journal cụ thể.
- Expand các `input` LaTeX để kiểm tra cả nội dung dùng chung. Tác giả trống;
  không có “MIM-LLM research program”, nhãn Q1/Q3 hoặc lời nói một bài phục vụ
  bài kiến trúc trong bốn manuscript. Mỗi bài có title/câu hỏi/controls/references
  và stop conditions riêng. Các slug thư mục cũ được giữ làm đường dẫn ổn định.
- JSON kế hoạch: A/B/C đều 24 runs, pilot 48M post-training targets. Warm-up
  dùng chung tính một lần; tổng pilot với toàn reserve **195,6M** và confirmation
  **948M** targets. Đây là trần kế hoạch, không phải số token đã train. Cap giờ
  GPU và overhead rollout/replay phải đo trước khi chốt so sánh compute-matched.
- minGRU **2.081.384**, Transformer **2.074.320** tham số đã instantiate/đếm;
  context 256 dùng để đếm, còn phải chọn context chứa đủ task. Kiến trúc residual
  chưa triển khai nên chưa có số tham số thực. Throughput/cost mới chưa đo.
- Xác minh lại SHA-256 cho **24 PDF nguồn** tải thành công. Một lần tải PDF
  timeout; bài đó chỉ dùng abstract/metadata. Undermind hoàn tất **168 candidate
  records**, không phải 168 bài đã full-text verified. Mức đọc ghi từng nguồn
  trong [source manifest](PORTFOLIO_V3_SOURCES.json).
- Kiểm tra liên kết của các Markdown thay đổi: **34 relative Markdown links**
  và **141 wikilinks trong 50 note Obsidian** đều trỏ tới file có
  thật. Không đưa vault hoặc Integration-Map nội bộ vào Git.
- `.venv/Scripts/python.exe -m mim_llm.cli paper-tracks` chạy thành công và khớp
  bốn track mới. `match_width` không đổi so với HEAD trước revision. Không sửa
  model, trainer hoặc evaluator; không chạy lại ML test suite cho thay đổi
  metadata/tài liệu này. Smoke tests cũ không xác nhận objective/router mới.
- `git diff --check` sạch; Git hiện không theo dõi PDF. Kiểm tra lại staged diff,
  repository public/chủ sở hữu/remote/default branch và SHA sau push.

Novelty gate vẫn mở, đặc biệt Q1 so với SEED và TreeWY/Flide. Chưa có training,
history bank, nhãn người, kết quả khoa học, funding approval hoặc mốc biên tập
mới. Bốn bản LaTeX là khung nghiên cứu có điều kiện, không phải bài đã hoàn tất.
