# Q3-A revision 2 — Kiểm tra tài liệu và phạm vi hoàn thành

Ngày 25/11/2026. Base commit trước thay đổi:
`0acd3356f4fad587c6602efd73632768effedfa4`.

## Những thay đổi đã hoàn tất

- Có đề cương hiện hành, JSON study-plan, LaTeX A và 10 câu hỏi bảo vệ revision 2.
- Đồng bộ README, bảng chương trình bốn bài, status và paper-tracks metadata.
- Định nghĩa A evaluation/B supervision/C mechanism evidence cùng hỗ trợ Q1;
  khai báo phần dùng chung, freeze scorer và source test mới cho Q1.
- Chuyển core A sang evaluator validation/inference-first; primary paired BA E2−E1
  đối chiếu human labels, không phải generator score; old120M là extension Q1/C.
- Giữ hồ sơ và nhật ký trước; thêm note v2 trong Obsidian, đánh dấu định hướng cũ
  là lịch sử. Chưa đổi scientific/editorial milestones.

## Kiểm tra đã chạy

- JSON parse, revision/title nhất quán với LaTeX; 96×2×2=384 planning outputs;
  supports Q1; training không bắt buộc; milestone flags đều false.
- Đủ 10 câu hỏi v2. Không U+FFFD; 25 relative Markdown links trong tập README,
  publication/status và tài liệu Q3-A trỏ tới file hiện có.
- Vault có 42 note của dự án; 73 wikilink được kiểm tra hợp lệ ở lần kiểm tra này.
- Hash CheckEval PDF khớp giá trị trong đề cương; không upload lại PDF lên repo.
- `python scripts/build_papers.py`: A/B/C PASS, 6/5/5 trang. Không undefined
  citations/references, overfull/underfull boxes hoặc build-console warning/error.
  Dùng bundled fonts.conf trong tiến trình kiểm tra; không đổi cấu hình toàn máy.
- Đã xem bản render đủ 16 trang; không thấy công thức/bảng tràn hoặc chữ bị cắt.
- `.venv/Scripts/python.exe -m mim_llm.cli paper-tracks` chạy exit 0, hiển thị
  đúng câu hỏi mới, trạng thái design-only và supports của A/B/C.
- `git diff --check` không có lỗi whitespace; thông báo LF→CRLF là quy tắc Git.

Không thêm unit test để kiểm tra các chuỗi planning; không thay model/train/
evaluator implementation và không chạy lại ML test suite cho sửa đề cương này.

## Những việc còn phải làm trước train/evaluation hoặc nộp

Evaluator E1/E2, schema v1 và annotation protocol mới chưa được triển khai/validated.
Chưa có source test mới, human labels, model weight download, actual parameter
count của judge, inference throughput/VRAM/cost hay kết quả khoa học mới. Prototype
MIM-LM và benchmark v0 không tự đáp ứng revision 2.

J.UCS scope/fee statement chung được tái kiểm tra trên official profile;
SCImago và full submission page trả HTTP 403, nên fresh quartile, phí phụ và
độ dài/template chưa đủ xác minh. Không có funding hay editorial approval mới.
Không có bảo đảm xác suất chấp nhận cao nhất. PDF chỉ lưu cục bộ; không rewrite
Git history. SHA sau push ghi trong nhật ký Obsidian.
