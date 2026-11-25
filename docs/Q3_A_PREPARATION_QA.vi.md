# Q3-A — Kiểm tra gói chuẩn bị viết, 25/11/2026

Phạm vi: tài liệu nghiên cứu, 10 câu hỏi đề cương, README, nguồn LaTeX và ghi chép
Obsidian. Không huấn luyện thêm, không thu nhãn người và không sửa benchmark code.

## Kiểm tra đã thực hiện

- Đủ 10 câu hỏi đánh số 1–10, có câu trả lời mẫu, bằng chứng cần có và giới hạn claim.
- Manifest có 17 key duy nhất; hash SHA-256 và số trang khớp 17 PDF cục bộ.
- 18 liên kết Markdown tương đối trong tập README/tài liệu Q3-A được kiểm tra đều
  tồn tại; không có ký tự thay thế U+FFFD trong tập kiểm tra.
- Vault có 40 note của dự án; 58 wikilink được kiểm tra trỏ tới note hiện có.
  Những con số này mô tả lần kiểm tra, không phải độ bao phủ của nghiên cứu.
- `python scripts/build_papers.py`: cả ba khung PASS. Q3-A 6 trang, Q3-B/C mỗi
  khung 5 trang. Không undefined citation/reference, overfull/underfull box hay
  cảnh báo/lỗi console ở lần build cuối. Đã xem bản render của cả 16 trang;
  không thấy bảng/công thức tràn hay chữ bị cắt. Các ô kết quả vẫn để trống.
- Lần build đầu có thông báo Fontconfig không tìm thấy cấu hình mặc định.
  Lần kiểm tra cuối đặt FONTCONFIG_FILE trong tiến trình PowerShell tới
  fonts.conf đi kèm Poppler của Codex runtime rồi build lại thành công. Không
  đổi cấu hình toàn máy, không che thông báo bằng lọc stderr.
- `git diff --check` không báo lỗi whitespace. Git báo quy tắc chuyển LF→CRLF;
  đó không phải lỗi LaTeX hay lỗi thí nghiệm.
- GitHub metadata xác nhận owner/repo `dakiemdarktharr/MIM-LLM`, public,
  default branch `main`; origin đúng URL dự án trước khi commit/push.

## Những điều lần kiểm tra này không chứng minh

Không chứng minh benchmark có validity, nhãn người đáng tin, mô hình viết được,
MIM hơn baseline, tính mới đủ đăng riêng, phí/hạng journal hiện hành hay UEH tài
trợ. Không có thí nghiệm khoa học mới. Không chạy lại ML test suite cho thay đổi
thuần tài liệu; kết quả 50 tests của phiên trước giữ nguyên ngày và phạm vi cũ.

PDF, bản trích text, hình render và helper script kiểm tra nằm trong artifacts/
hoặc output/ cục bộ, bị Git ignore. Chỉ nguồn Markdown/JSON/LaTeX được version.
Không rewrite Git history. Mốc bản thảo có kết quả, nộp, chấp nhận, xuất bản vẫn
chưa đạt. Commit SHA cuối được ghi trong nhật ký Obsidian sau khi push xác minh.
