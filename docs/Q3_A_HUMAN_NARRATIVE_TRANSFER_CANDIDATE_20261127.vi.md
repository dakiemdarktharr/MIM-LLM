# Ứng viên transfer truyện do người viết — 27/11/2026

Tra có mục tiêu trong lúc foundation chạy; **chưa thu dataset, chọn test stories,
tạo intervention hoặc gán nhãn**. Không thay corpus/tokenizer/plan c18.

Nguồn chính đã kiểm:

- [FairytaleQA,ACL2022](https://aclanthology.org/2022.acl-long.34/), DOI
  `10.18653/v1/2022.acl-long.34`: bài đã phản biện. Đọc abstract và các đoạn
  §3.1–3.3 của [PDF](https://aclanthology.org/2022.acl-long.34.pdf), chưa đọc toàn
  bộ14trang.278truyện cổ tích lấy từ Project Gutenberg, có chỉnh từ cổ/dấu câu;
 10.580QA do chuyên gia giáo dục tạo. Đơn vị nguồn phải là truyện, không câu/QA.
- [Repo tác giả](https://github.com/uci-soe/FairytaleQAData) hiện chuyển tới
  `uci-edu/FairytaleQAData`; [LICENSE](https://github.com/uci-edu/FairytaleQAData/blob/main/LICENSE)
  ghi Apache2.0. Đây là bằng chứng license repo, chưa thay kiểm provenance/quyền
  của từng bản truyện nguồn. Chưa pin revision hoặc xác minh từng story/translator.
- [Florescu etal.,HumEval2024](https://aclanthology.org/2024.humeval-1.10/):
  metadata/abstract cho thấy một nghiên cứu tái lập đánh giá người trên QAG với
  FairytaleQA. Chưa audit toàn PDF; không suy ra agreement hoặc kết luận số cụ thể.

Truy vấn: `FairytaleQA dataset license GitHub official`; `FairytaleQA human
written stories 278 narrative temporal causal dataset license`, ưu tiên ACL
Anthology/repo chính chủ. Đây là3hồ sơ nguồn, không3công trình trùng phương pháp;
2bài được xác minh metadata, không tuyên bố systematic review hoặc đã đọc đủ.

## Ảnh hưởng tới thiết kế — đề xuất của dự án

Không dùng QA gốc làm gold label cho prose tiếp nối. Các QA ngắn chỉ gợi vị trí
có quan hệ hành động/nhân quả; nhiệm vụ chính vẫn3–5câu và nhiều tiếp nối hợp lệ.
Nếu thêm giờ/quy tắc/ghi đè để tạo cặp controlled, gọi rõ **adapted narrative
transfer**, ghi phần đã sửa và không coi cặp mới là hoàn toàn do người viết.

Trước khi chấp nhận một story: pin commit/data hash, tác giả/dịch giả/edition,
URL và điều kiện dùng lại; lưu attribution/notice; kiểm overlap theo nguồn và
chuỗi chuẩn hóa với train/validation; kiểm thêm semantic/fairy-tale familiarity
thay vì tuyên bố chưa từng thấy chỉ nhờ exact dedup. Các bước này chưa hoàn tất.

Đăng ký tiêu chí chọn truyện trước khi xem output model: đoạn tự đủ ngữ cảnh,
có trạng thái/hành động giải nghĩa được, context đủ và phép đổi tiền đề có hậu
quả rõ. Chọn theo tiêu chí/nguồn, không theo việc model nào trả lời thuận giả
thuyết. Giữ cả outcome không cải thiện và trường hợp không chuyển được từ template.

Hiện chỉ có tác giả sinh viên làm reader. Không dùng nhãn chuyên gia FairytaleQA
để giả một reader độc lập cho output mới. Sau writing feasibility, cần đo thời
gian gán nhãn thực trên packet mù rồi chốt sample/power/resource; chưa có đủ
bằng chứng cho một lịch hoàn tất paper hoặc human validation. Nếu nguồn này
không đáp ứng context/quyền/provenance, loại ứng viên theo tiêu chí đã ghi.

## Kiểm kê metadata có pin, chưa nhập nội dung truyện

Pin repo `uci-edu/FairytaleQAData` tại
`a24ddc17364666b7c13a425b9970c87368b03417`, Git tree
`93b6c8fc9fa312cc15baf26edcc5c4f3fd6c19f1` (không truncated).
Đọc [story_meta.csv](https://github.com/uci-edu/FairytaleQAData/blob/a24ddc17364666b7c13a425b9970c87368b03417/story_meta.csv),
[README](https://github.com/uci-edu/FairytaleQAData/blob/a24ddc17364666b7c13a425b9970c87368b03417/README.md)
và toànLICENSE qua GitHub connector; chỉ lưu3files này và CSV tree inventory
trong `data/raw/fairytaleqa-a24ddc173646/`, được Gitignore. Chưa tải corpus truyện
hoặc QA, chưa token hóa, chọn đoạn hay tạo model output/nhãn.

`scripts/audit_fairytaleqa_source_metadata.py` kiểm nguyên bytes với Git blob
SHA1 có pin rồi ghi SHA256. Bản đầu materializeLICENSE đã mất whitespace cuối
và bị kiểm hash từ chối; đã sửa bằng exact bytes, không bỏ kiểm tra. Manifest
`configs/q3a/fairytaleqa_source_audit.json` là source audit, không final transfer.

Kết quả từ metadata:278story IDs,15origin-book groups; upstream232train/23val/
23test. Tổng declared4095sections/598613words/10580questions **chưa đếm lại từ
nội dung**. `child-of-mary` và `farquhar-macneill` ghi0words; không dùng0làm
độ dài thật để lựa chọn. Metadata đường dẫn `snow-man` khác case file `Snow-man`.
`farquhar-macneill` có blob origin a5163829…/7343bytes, split c1c04032…/7332bytes;
chưa đọc nội dung để giải thích khác biệt. Các bản trong folder `all` là view
trùng chủ ý, không split độc lập; audit so với đúng split của từng dòng.

Metadata chỉ có filename/origin/split/sections/words/questions; chưa giải quyết
Gutenberg ID/edition/dịch giả/quyền từng sách. Không tự suy ra license mọi bản
truyện từLICENSE repo. Trước transfer cần chọn một representation cụ thể, kiểm
source rights/overlap/context và ngữ nghĩa bằng người thật; giữ provenance từng
đoạn sửa.15book groups cũng cần được xét như cấu trúc phụ thuộc khi đăng ký
ước lượng uncertainty; không coi hàng nghìn sections/QA là các nguồn độc lập.

Lệnh audit đọc files đã được pin, không truy cập model hoặc train:

```powershell
.venv/Scripts/python.exe scripts/audit_fairytaleqa_source_metadata.py --directory data/raw/fairytaleqa-a24ddc173646 --output NEW_METADATA_RECEIPT.json
```
