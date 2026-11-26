# Q3-A: nguồn chuyển giao ngoài template — 26/11/2026

**Đã kiểm tra ba ứng viên; chưa có cặp chuyển giao được người thật duyệt.**
Tải được corpus hoặc xác minh license chưa chứng minh task chuyển giao hợp lệ.
Không đưa những nguồn này vào train, không mở test đã khóa và không đổi bundle.

| Nguồn chính chủ | Bằng chứng nguồn/giấy phép | Phù hợp và quyết định hiện tại |
|---|---|---|
| [Natural Stories](https://github.com/languageMIT/naturalstories), [bài gốc](https://pmc.ncbi.nlm.nih.gov/articles/PMC8549930/) | Repo pin `4700daad696e942f5aba23c957a7423d0de66612`; LICENSE.txt ghi CC BY-NC-SA 4.0. Truyện được người biên tập để có cấu trúc cú pháp ít gặp, không phải mẫu ngẫu nhiên của truyện tự nhiên. | Có thể dùng làm nguồn đoạn truyện, nhưng cần kiểm tra ngữ nghĩa và điều kiện dùng/chia sẻ bản phái sinh. Chỉ có 10 cụm truyện gốc; không coi hàng trăm cửa sổ là hàng trăm truyện độc lập. |
| [ProPara](https://github.com/allenai/propara), [bài gốc](https://arxiv.org/html/1805.06975) | Bài mô tả 488 đoạn quy trình do người viết, gán nhãn tồn tại/vị trí. Repo pin `51a3cccbedcbe5f92276f9925e0ce1e6ec4247bb`, LICENSE Apache-2.0; điều kiện của gói data ngoài repo chưa đối chiếu xong. | Nguồn chẩn đoán state tracking dạng quy trình, không tự là story generation. Không lấy license code làm bằng chứng đầy đủ cho mọi data package; chưa nhập dữ liệu làm test. |
| [TRIP chính chủ](https://huggingface.co/datasets/sled-umich/TRIP/blob/main/README.md), [bài gốc đã phản biện](https://aclanthology.org/2021.findings-emnlp.422/) | Card ghi ngôn ngữ crowdsourced nhưng `license: []`; repo `sled-group/Verifiable-Coherent-NLU` pin `a50f08c77a81456e9f6bb0d85bc1d7400bc827cc` không có LICENSE ở danh sách root đã kiểm tra. | Cặp plausible/implausible và state evidence gần kiểm tra logic thành phần; không mặc định là bài sinh tiếp truyện. Chưa đủ căn cứ license để nhập/phân phối corpus vào benchmark. |

Các truy vấn: “ProPara dataset human authored procedural paragraphs github
license”, “TRIP dataset tiered reasoning intuitive physics human authored stories
license github”, “Natural Stories corpus license MIT github human written stories
CC BY”. Tra nguồn bài gốc, repo tác giả và dataset card chính chủ. Đây là kiểm
tra ba ứng viên cụ thể, không phải khảo sát toàn bộ dữ liệu đang tồn tại.

## Đã đo trực tiếp từ bản Natural Stories được pin

Tải công khai LICENSE.txt, README.md và words.tsv vào
`data/raw/naturalstories-4700daad696e/`; không đăng corpus lên GitHub. Chỉ lấy
dòng có mã `story.position.whole` để kiểm kê, kiểm tra vị trí duy nhất/liên tục.

- 10 story IDs; tổng 10.256 đơn vị `.whole`. Đây là cách đếm file thực tế,
  **không phải** số lexical words của bài báo và không phải token byte của LM.
- Ghép các đơn vị bằng dấu cách cho mỗi truyện: 5.209–6.538 byte UTF-8/truyện.
  Cả mười truyện vượt context 2.048 byte-token nếu dùng nguyên văn toàn bộ.
- SHA256 words.tsv:
  `0955415234babe7fe6890e447d96a2520175f5ea2b8eb130bd31e6aea94e4495`.
- SHA256 LICENSE.txt:
  `58032a8173195237068ab02d429948bc3233d8e6858d1b9ddfdc47e3bbc3d847`.
- SHA256 README.md:
  `02fcc9104a8887c3f67e1be47d17a7253476628dbacde3fccec67a76deef285f`.

URL để tái tải có pin:
`https://raw.githubusercontent.com/languageMIT/naturalstories/4700daad696e942f5aba23c957a7423d0de66612/words.tsv`.
Giữ nguyên license/attribution và công bố thao tác ghép/cắt/sửa. Không gắn license
của code dự án hoặc CC BY của bài báo lên corpus/bản phái sinh một cách ngầm định.
Không tải reading-time/participant records vì task này không cần chúng. Repo có
correction năm 2025 về reading-time alignment; không dùng số RT làm kết quả Q3-A.

## Cách biến nguồn ứng viên thành phép đo hợp lệ

1. Chọn đoạn tự chứa đủ tiền đề; bỏ đoạn cần hồi chỉ hoặc tri thức ngoài phạm vi
   chưa được khai báo. Kiểm tra **prompt hoàn chỉnh cộng generation reserve**
   theo tokenizer byte, không cắt tùy tiện để vừa context. Định dạng tiếng Anh
   và yêu cầu sinh 3–5 câu được giữ; chưa chốt độ dài khi chưa có prompt thật.
2. Người thật kiểm tra từng chỉnh sửa effective/no-op: nghĩa nào buộc đổi,
   nghĩa nào buộc giữ, mốc thời gian và cách diễn giải thay thế. AI/code có thể
   hỗ trợ đề xuất nhưng không được ghi thành nhãn đã được người xác nhận.
3. Không chèn nguyên mẫu tủ/điện vào một đoạn mới rồi gọi đó là chuyển giao
   naturalistic. Nếu sửa nguồn, công bố rõ human-authored prefix và phần
   AI/human chỉnh sửa. Không biến task thành lựa chọn nhãn hoặc chỉ hỏi tên.
4. Rubric gốc có `holder/action/cabinet/reason` **chưa bao quát** các truyện này.
   Cần schema mệnh đề tổng quát và rubric phù hợp, được pilot hai người đọc.
   Không đổi tên mọi state thành “cabinet” để làm analyzer hiện tại chạy qua.
5. Giữ mọi cửa sổ/cặp cùng truyện gốc trong một split và một cụm bootstrap.
   Với chỉ 10 cụm, báo giới hạn precision; nhiều output không tăng số truyện
   độc lập. Không gộp với 400 nguồn synthetic để che bất định chuyển giao.
6. Chốt nguồn, chỉnh sửa, nghĩa bắt buộc, decoding, mẫu và phân tích trước khi
   sinh output test; giữ output lỗi/chung chung trong denominator. Báo riêng
   transfer và controlled benchmark. Không dùng transfer test chọn cấu hình.

File `configs/q3a/transfer_sources.candidates.json` chỉ ghi provenance và trạng
thái ứng viên. Không dùng nó điền `naturalistic_transfer_manifest` như thể tập
chuyển giao đã hoàn tất. Nếu không xây được phép đo đúng nghĩa/đủ precision,
giữ limitation và thu hẹp claim, không đổi tiêu chí sau khi xem kết quả.
