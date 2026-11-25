# Q3-A — Hồ sơ nghiên cứu để chuẩn bị viết

Ngày rà soát: **25/11/2026**, múi giờ Việt Nam. Trạng thái: **research planning**.
Đây là tổng hợp tài liệu và đề xuất protocol; chưa có kết quả khoa học, nhãn người
đọc hay bản thảo hoàn chỉnh. Tên Q3-A là mục tiêu của chương trình, không phải hạng
đã được một tạp chí xác nhận cho công trình.

## 1. Quyết định sau khảo sát

**Nên làm pilot xác thực phép đo trước khi train lớn.** Không nên định vị bài là
“benchmark đầu tiên về phản thực tế/nhất quán trạng thái trong truyện”. Những phần
đó đã có tiền lệ rất gần. Câu hỏi hẹp hơn, có thể kiểm chứng là:

> Khi giữ tương đương độ dài và thông tin đầu vào, việc phải kết hợp trạng thái
> còn hiệu lực với quy tắc có thời điểm áp dụng gây ra những lỗi nào trong đoạn
> tiếp nối 3–5 câu mà bài kiểm tra một dữ kiện cuối truyện chưa bộc lộ?

Tiêu đề làm việc giữ nguyên: **Temporal Conditions, State Overwrites, and
Counterfactual Invariance in Autoregressive Story Continuation**. Có thể đổi thành
**From Entity Probes to Story Continuation: Diagnosing Temporal State Consistency**
nếu bằng chứng chính thực sự là khoảng cách giữa hai cách đánh giá.

Đóng góp phải gồm: (i) đặc tả ngữ nghĩa kiểm tra được; (ii) bằng chứng về độ tin cậy
và giá trị của phép chấm; (iii) phát hiện thực nghiệm có ích sau khi kiểm soát mẹo
bề mặt, độ dài và khả năng viết. Ghép nhiều yếu tố đã biết vào một bộ dữ liệu
không tự động tạo ra tính mới. Q3-A vẫn có thể có giá trị khi MIM không thắng.

## 2. Phạm vi tìm và mức độ đọc

Đã tải **17 PDF nguồn chính**, đối chiếu metadata và đọc các phần liên quan;
không tuyên bố đã đọc từng dòng của cả 17 bài. Trong tập này, 16 nguồn nằm trong
kỷ yếu/tạp chí phản biện, ScratchWorld được dùng với trạng thái **preprint**.
Xem [sổ nguồn và dấu vết truy xuất](Q3_A_SOURCE_LEDGER.vi.md) để biết URL, phần đã
đọc, hash PDF, truy vấn và giới hạn khảo sát.

Undermind đã được thử cho lượt tìm mới, nhưng tài khoản hết hạn mức miễn phí;
lượt mới **chưa chạy**. Công cụ báo mở lại lúc 14:00 UTC, tức 21:00 Việt Nam ngày
25/11/2026. Kết luận ở đây dựa vào nguồn trực tiếp từ ACL Anthology, arXiv, tài
liệu/repo tác giả và kiểm tra mã hiện có. Đây không phải một systematic review
bao phủ toàn bộ tài liệu đến ngày tra; không suy ra “chưa có ai làm” từ tập nguồn
đã tìm. Chưa tiến hành điều tra riêng về công trình tại Việt Nam trong lượt này.

## 3. Những công trình buộc ta thu hẹp phát biểu tính mới

| Nguồn đã xác minh | Điều thực sự đã có | Hệ quả cho Q3-A — suy luận thiết kế của chúng ta |
|---|---|---|
| [TIME TRAVEL, EMNLP-IJCNLP 2019](https://aclanthology.org/D19-1509/) | Viết lại kết thúc truyện theo tiền đề phản thực tế, giữ phần phù hợp; đánh giá tôn trọng điều kiện mới và cốt truyện. | Không nhận là người đầu tiên sinh truyện phản thực tế hay giữ dữ kiện bất biến. Tiếp nối mở khác chỉnh sửa kết thúc, nhưng khác định dạng chưa đủ thành đóng góp. |
| [Paul & Frank, Findings EMNLP 2020](https://aclanthology.org/2020.findings-emnlp.267/) | Counterfactual Invariance Prediction: phân loại sự kiện sau đó còn đúng hay không khi đổi tiền đề; dữ liệu lấy từ TIME TRAVEL. | Chấm invariant là kế thừa rõ ràng; cần thêm bằng chứng chẩn đoán trong văn bản sinh và trạng thái theo thời điểm. |
| [PASTA, TACL 2023](https://aclanthology.org/2023.tacl-1.73/) | Trạng thái của nhân vật, nhiễu phản thực tế và sửa truyện; đánh giá người đọc về suy ra trạng thái và tính hợp logic, kể cả chỉ số ALL. | “Tất cả yêu cầu đều đúng” không phải phát minh mới. Phải so với cơ chế state-conditioned revision và giải thích phần giao nhau. |
| [Entity Tracking, ACL 2023](https://aclanthology.org/2023.acl-long.213/) | Theo dõi đối tượng qua chuỗi thao tác và truy vấn trạng thái cuối. | Là phép kiểm tra thành phần; cần đo xem thành công ở đó có chuyển sang viết đoạn hay không. |
| [Naturalistic entity tracking, EMNLP 2026](https://aclanthology.org/2026.emnlp-main.2231/) | Truyện tạo bằng template có vẻ tự nhiên; độ phức tạp/độ gần lần nhắc được kiểm tra; truy vấn vị trí cuối và probability readout. | Không mô tả nhầm là dữ liệu hoàn toàn do người viết. Đánh giá explicit một từ khác đoạn 3–5 câu, nhưng tác giả đã xử lý nhiều lo ngại về recency. |
| [FactTrack, NAACL 2025](https://aclanthology.org/2025.naacl-long.144/) | Biểu diễn sự kiện có khoảng hiệu lực theo thời gian, phát hiện mâu thuẫn trong outline. | Dùng tư duy khoảng hiệu lực; không chấm một lần đổi vị trí hợp lệ thành mâu thuẫn. Bảng trạng thái/sửa văn bản ngoài backbone là điều kiện khác. |
| [ConStory-Bench, Findings ACL 2026](https://aclanthology.org/2026.findings-acl.410/) | Kiểm tra mâu thuẫn trong truyện dài do mô hình sinh, phân loại lỗi và dẫn chứng. | “Nhớ sự kiện mình vừa viết” đã có hướng gần. Niche của ta phải là can thiệp có đối chứng và ngữ nghĩa kiểm tra được, không chỉ độ dài ngắn hơn. |
| [ScratchWorld v2, 28/10/2026 — preprint](https://arxiv.org/abs/2606.31689) | Hệ thực thi cho nhãn, phân biệt trường thay đổi với trường giữ nguyên, các đối chứng không hành động/copy trạng thái. | Không gộp invariant chiếm đa số để che lỗi cập nhật; chưa xem kết quả preprint là kết luận đã được phản biện. |
| [A Causal Approach…, ACL 2024](https://aclanthology.org/2024.acl-long.354/) | Sinh phản thực tế dùng VAE, classifier và tri thức sự kiện; nêu nguy cơ khai thác mẫu đặc thù của dữ liệu. | Không nhận “sinh có quan hệ nhân quả” là mới; benchmark phải chống được mẹo copy/paraphrase. |
| [ConWriter, Findings EMNLP 2026](https://aclanthology.org/2026.findings-emnlp.359/) | Bộ điều khiển không train: memory ngoài, kiểm tra chuyển trạng thái và sửa cục bộ trong sinh truyện dài. | Phân biệt backbone thuần với hệ có bảng trạng thái/repair tại inference. Không trình bày bộ điều khiển ngoài như một phép đo bộ nhớ ẩn. |
| [ChronoScope, ACL 2026](https://aclanthology.org/2026.acl-long.2133/) | Kiểm tra giữ/đổi/chuyển phạm vi thời gian qua nhiều lượt hỏi, trên chuỗi từ Wikidata. | Khoảng cách giữa đúng một câu hỏi và nhất quán qua chuỗi cũng đã được nghiên cứu. Phần của ta phải chứng minh ở tiếp nối văn bản mở với quy tắc và lịch sử trạng thái, không nhận phát hiện chung này là mới. |

Các nền tảng phương pháp khác: [TRIP](https://aclanthology.org/2021.findings-emnlp.422/)
liên kết quyết định, cặp mâu thuẫn và trạng thái giải thích;
[ProPara](https://aclanthology.org/N18-1144/) theo dõi tồn tại/vị trí trong quy trình;
[CheckList](https://aclanthology.org/2020.acl-main.442/) có minimum functionality,
invariance và directional expectations. Q3-A kế thừa các tư tưởng này, không đổi
tên thành đóng góp mới.

Sàng lọc thêm ở mức abstract: [CEval, INLG 2024](https://aclanthology.org/2024.inlg-main.6/)
là đổi văn bản để nhãn classifier thay đổi, không đồng nhất với can thiệp sự kiện
trong truyện; [ChronoQA/E2RAG, EACL 2026](https://aclanthology.org/2026.eacl-long.90/)
là hỏi đáp trên tài liệu truyện có retrieval; [TRACE, Findings EMNLP 2026](https://aclanthology.org/2026.findings-emnlp.1045/)
là temporal knowledge editing. Đây là các hướng liên quan, chưa được full-text
audit trong lượt này; không đánh đồng các nghĩa của “counterfactual” và “memory”.

## 4. Thuật ngữ và hợp đồng ngữ nghĩa

- **Trạng thái** là giá trị đang có hiệu lực, ví dụ ai giữ chìa ở một thời điểm.
  **Sự kiện** làm thay đổi hoặc kiểm tra trạng thái, ví dụ giao chìa thành công.
- **Ghi đè** là cập nhật một thuộc tính đã có giá trị; không phải tăng số lần nhắc
  tên hoặc số câu. Phải ghi rõ depth tính số chuyển trạng thái thành công nào.
- **Phản thực tế** ở đây là chạy lại cùng tình huống theo một tiền đề được thay,
  giữ phần còn lại của hợp đồng. Không phải tự do sáng tác một thế giới khác.
- **Invariant** là mệnh đề không đổi dưới can thiệp đã chỉ định, không phải một
  sự thật phải giữ nguyên ở mọi thời điểm về sau.
- **Oracle** là chương trình suy ra đáp án đúng từ mô hình sự kiện đã đặc tả.
  Nó đảm bảo nhãn của thế giới mô phỏng, không tự đảm bảo mọi câu tự nhiên đã được
  trích xuất/diễn giải đúng.

Đề xuất biểu diễn trạng thái \(s^{w}_{t,k}\), trong đó \(w\) là thế giới thật/giả
định, \(t\) là giờ, \(k\) là thứ tự vi sự kiện cùng giờ. Một sự kiện hợp lệ cập
nhật \(s^{w}_{t,k+1}=T(s^{w}_{t,k},e_{t,k})\). Mệnh đề có dạng
\(p=(w,t,k,\text{attribute},\text{value})\); nhờ vậy “tủ mở ở thế giới thật” và
“tủ khóa ở thế giới giả định” không bị gộp thành mâu thuẫn.

Với bài tủ, phải công khai các giả định sau trong dữ liệu/rubric:

1. Tủ khóa ngay trước lần đánh giá quy tắc; không có cách mở khác trong khoảng
   đang kiểm tra. Mọi lần giao được mô tả là thành công và xảy ra trước 9:00.
2. Tất cả nhân vật tuân thủ quy tắc. Từ “phải mở” là nghĩa vụ; **nghĩa vụ không
   tự suy ra hành động thực tế** nếu chưa giả định tuân thủ.
3. Quy tắc “đúng 9:00” được kiểm tra một lần. Mất điện lúc đó dẫn tới chờ, tủ
   khóa tại 9:00. Không tự suy ra chắc chắn mở lúc 9:05; đó cần quy tắc bổ sung.
4. Đề nghị pilot loại trường hợp điện về đúng 9:00. Nếu thêm sau này, xác định
   thứ tự điện về/kiểm tra quy tắc, không để người chấm tự chọn.
5. Người **giữ chìa** không nhất thiết là người **sở hữu** chìa. Sau khi đặt chìa
   vào ngăn kéo, trạng thái vị trí đổi; Mai không phải giữ chìa mãi mãi.
6. Phần viết tiếp bắt đầu ở thời điểm quyết định, không được bịa ngược một hành
   động mở tủ trước đó để vô hiệu hóa tiền đề.

Đây là ngữ nghĩa của một microworld có quy tắc công khai. Kết quả không chứng
minh mô hình phát hiện quan hệ nhân quả trong thế giới thật hay có “world model”
tương đương con người.

## 5. Một cặp minh họa và các trường hợp không có đáp án duy nhất

**Minh họa do người soạn hồ sơ viết, không phải đầu ra mô hình hay nhãn người đọc
đã thu thập.** Prefix: tủ khóa; Lan giữ chìa rồi đưa Huy, Huy gửi Mai; tất cả tuân
thủ quy tắc đúng 9:00 mở nếu đã có điện, nếu chưa có điện thì chờ. Điện về 8:55.

> Đúng 9 giờ, Mai mở tủ vì điện đã trở lại. Cô đặt chìa vào ngăn kéo bên cạnh rồi
> sắp xếp đồ trong tủ. Khi Lan hỏi chìa ở đâu, Mai chỉ cô tới ngăn kéo. Nếu điện
> về muộn hơn mười phút, lúc 9 giờ Mai phải chờ và tủ vẫn khóa.

Đổi duy nhất **8:55 → 9:05** trong prefix:

| Mệnh đề có chỉ số thời gian/thế giới | Prefix 8:55 | Prefix 9:05 |
|---|---|---|
| Mai giữ chìa ngay trước hành động theo quy tắc lúc 9:00 | Đúng | Đúng |
| Chuỗi giao trước 9:00: Lan → Huy → Mai | Đúng | Đúng |
| Điện đã về khi quy tắc được kiểm tra | Đúng | Sai |
| Hành động được quy tắc buộc tại 9:00 | Mở | Chờ |
| Tủ mở ngay sau hành động tại 9:00 | Đúng | Sai |
| Địa điểm Mai tự chọn cất chìa sau đó | Tự do, phải nhất quán trong nhánh đó | Tự do, phải nhất quán trong nhánh đó |

Prefix 9:05 có yêu cầu “muộn hơn mười phút” thì nhánh giả định là **9:15**, không
phải 9:05. Cả 9:05 và 9:15 đều chưa có điện lúc 9:00. Không ép hai nhánh tự do
phải chọn cùng ngăn kéo: chỉ những invariant được định nghĩa mới bắt buộc giữ.
Không nói vị trí chìa không có nghĩa là vị trí ấy sai; nhưng bỏ một mệnh đề bắt
buộc làm giảm coverage. Phải tách **thiếu thông tin**, **mơ hồ** và **mâu thuẫn**.

## 6. Giả thuyết và đối nghịch hợp lý

| Giả thuyết dự kiến, chưa đăng ký trước | Thiết kế phân biệt | Kết quả chống lại cách giải thích mong đợi |
|---|---|---|
| H1: nhiều cập nhật liên quan làm tăng lỗi trong đoạn sinh, khi độ dài được giữ tương đương. | So depth thấp/cao trên nguồn ghép cặp; kiểm soát độ xa lần cập nhật cuối, số đối tượng và độ dài. | Lỗi chỉ đi theo độ dài/khả năng viết, hoặc không đổi theo depth với CI đủ hẹp. |
| H2: trả lời đúng probe chưa đủ để viết tiếp đúng. | Cùng thông tin, hai tác vụ chạy riêng; bảng 2×2 probe đúng/sai và continuation đúng/sai. | Chênh lệch chỉ do format/instruction; sau kiểm soát fluency không có chẩn đoán thêm. |
| H3: mô hình có thể đổi hệ quả nhưng làm hỏng invariant, hoặc giữ mọi thứ và không cập nhật. | Cặp effective và no-op; báo changed và preserved riêng. | Các thước đo đơn giản có sẵn giải thích đầy đủ, metric mới không thêm giá trị. |

Giả thuyết đối nghịch chung: một phép đọc lại ngữ cảnh đủ tốt cộng khả năng làm
theo hướng dẫn giải thích kết quả; không cần bộ nhớ đặc biệt. Q3-A không kiểm
định ưu thế kiến trúc MIM. Nghiên cứu đó thuộc Q1/Q3-C với điều kiện thông tin và
tài nguyên tương đương. Không chọn test, metric hay seed vì MIM được lợi.

## 7. Kiểm tra mã pilot: đã có gì và còn thiếu gì?

Rà `src/mim_llm/benchmark.py`, `oracle.py`, `evaluation.py` ngày 25/11/2026 trên
base commit `68e8344afeca39f339b30c404b4618bca12e9c0c`:

| Đã có trong v0 | Giới hạn phải xử lý trước nghiên cứu chính |
|---|---|
| Cặp đổi một giờ, oracle, depth mặc định 2–5, split theo source ID. | Chỉ 8:55/9:05, một ngưỡng 9:00; tất cả source cùng họ template. Hash ID không chứng minh khái quát cấu trúc. |
| Chuỗi giao chìa với tên được sample không lặp. | Người giữ cuối luôn là người nhận cuối. Không có quay lại người cũ, chuyển thất bại hay vật gây nhiễu. Last-recipient + clock-threshold có thể giải bài. |
| Cả actual và relative counterfactual có nhãn cấu trúc. | Phải audit annotation actual/CF/pair nhất quán; không nhầm 9:05→9:15. |
| Primary all-required + sentence format + no contradiction. | Cần thêm semantic-only metric; “concrete event” phải là sự kiện mới làm đổi trạng thái, không chỉ hành động bắt buộc hoặc câu có động từ. |
| Bootstrap theo source cho từng system. | Chưa có CI cho hiệu số hai hệ thống bằng cùng lần resample; CI riêng của hai hệ không thay cho CI paired delta. |
| Pipeline annotation và self-event. | Chưa có nhãn người thật, validation rubric, natural test được khóa hay kết quả nghiên cứu hoàn chỉnh. |

Các kiểm thử kỹ thuật đã qua trước đây không xác thực construct của benchmark.
Hồ sơ này **không sửa code benchmark**, không tuyên bố các phần còn thiếu đã được
triển khai. Phải version schema mới, giữ v0 cho smoke test.

## 8. Thiết kế pilot ít tốn nhất

Trước hết chuẩn bị 12–24 **cặp development** để kiểm tra ngữ nghĩa và nhãn; số này
không đủ kết luận so sánh model. Cân bằng:

- Can thiệp **effective** đi qua ngưỡng quyết định và **no-op** ở cùng phía ngưỡng,
  ví dụ 8:50→8:55. No-op kiểm tra mô hình có đổi kết quả một cách máy móc không.
- Ghi đè thật so với câu gây nhiễu cùng độ dài; có quay lại người cũ, nhiều vật,
  người được nhắc cuối không giữ vật, chuyển dự định/không thành công nếu rubric
  đã định nghĩa. Chỉ thêm từng cơ chế khi có nhãn rõ ràng.
- Tách độ sâu cập nhật {1,3,5}, độ gần lần cập nhật cuối {gần,xa} và loại can thiệp.
  Không mở mọi tổ hợp cùng lúc trước khi kiểm tra chi phí và độ tin cậy.
- Giữ cả họ cấu trúc/template ngoài train, không chỉ thay tên. Audit trùng nguồn,
  câu gần trùng và paraphrase. Test cuối khóa sau validation, trước chọn cấu hình.

Chạy đối chứng rẻ **last-recipient**, **last-mentioned person**, **always-open**,
**always-wait**, **clock-only**, **copy/no-change**. Nếu các mẹo này đạt gần bằng hệ
có năng lực và không có phân tích mới, phải sửa benchmark trên development.

Sau đó dùng một mô hình mở đã có khả năng viết làm **capability reference** tại
máy, chẳng hạn xem xét [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct).
Đây là gợi ý để thử, chưa đo chất lượng hay VRAM trên bài này. Không trộn nó vào
kết luận resource-matched của mô hình ~2M; dữ liệu pretrain/tokenizer của nó khác.
Nếu tất cả mô hình nhỏ chỉ sinh vụn câu thì chưa thể diễn giải lỗi là lỗi logic.

Matrix 4 kiến trúc × 3 seed × 10M targets/run = **120M training targets** là trần
pilot đã dự kiến, không phải mức dữ liệu bảo đảm bài đăng được. BPE-512 MIM-LM
tham chiếu có **2,081,472 tham số**; bản byte có **1,984,320**. Baseline pair cùng
width không tự khớp tham số; phải điều chỉnh và báo số thực cho từng run.

## 9. Chấm văn bản mở mà không ép một đáp án mẫu

Với đoạn \(i\), \(R_i\) là tập mệnh đề bắt buộc có chỉ số thế giới/thời điểm;
\(A_i\) là tất cả mệnh đề ấy được thể hiện đúng; \(F_i\) là đúng 3–5 câu;
\(C_i\) là có mâu thuẫn với prefix hoặc lịch sử đã sinh trong cùng nhánh.
Giữ primary đang đề xuất:

\[
Y_i=\mathbf{1}[A_i\land F_i\land\neg C_i],\qquad
\widehat P=\frac{1}{n}\sum_iY_i.
\]

Đồng thời báo **semantic-only** \(\mathbf{1}[A_i\land\neg C_i]\), format compliance,
coverage \(\#\text{mệnh đề bắt buộc đúng}/|R_i|\), lỗi theo loại và fluency riêng.
Không đổi primary sau khi nhìn test. Một primary contrast cần chốt trước:
đề xuất hiệu số strict-success depth cao–thấp trong các nhóm nguồn ghép cặp,
với độ dài/recency tương đương. Đây còn là đề xuất, chưa preregistration.

Với cặp, tính tỷ lệ toàn cặp hợp lệ và accuracy của mệnh đề **bắt buộc đổi** so
với mệnh đề **bắt buộc giữ**. Chỉ đổi từ ngữ không đủ là đổi hệ quả; đổi đúng giá
trị nhưng gán sai thế giới/thời điểm không được credit. Không lấy trung bình
gộp nơi invariant áp đảo. Một tập không có mệnh đề thuộc loại nào thì báo N/A và
denominator, không tự cho 100%.

Oracle kiểm tra event ledger; người chấm đọc prefix + output và chỉ ra bằng chứng
văn bản. Regex/exact match không đủ cho phủ định, đại từ và điều kiện. Dùng LLM
judge chỉ sau validation trên mẫu có lỗi gieo chủ đích **và** lỗi phát sinh tự
nhiên, báo false-positive/false-negative theo loại. Không mặc định judge hay người
chấm là không sai. [OpenMEVA](https://aclanthology.org/2021.acl-long.500/) là tiền
lệ đánh giá metric truyện, không phải chứng cứ rằng mọi judge hiện tại đều kém.

**Self-event:** sinh đoạn đầu rồi cố định raw token IDs; người chấm ghi trạng thái
mới thật sự được viết; yêu cầu tiếp nối có sử dụng trạng thái đó. Đếm sự kiện mới
có hiệu lực bền, tỷ lệ tạo sự kiện, tỷ lệ nhất quán có điều kiện và tỷ lệ thành
công vô điều kiện. Sự nhất quán với một lỗi đầu tiên không xóa lỗi so với prefix.
Nếu mô hình không tạo sự kiện hoặc chỉ nói chung chung, không tính là nhớ đúng.
Cho model đọc lại toàn lịch sử là bài kiểm tra hành vi với ngữ cảnh có sẵn;
**chưa chứng minh bộ nhớ ẩn nội tại**. Thiết kế carry-state/no-reread là thí nghiệm
khác và phải kiểm soát thông tin cho mọi kiến trúc.

## 10. Nhãn người đọc và thống kê

Hai người đọc được hướng dẫn bằng development, chấm độc lập và mù tên model;
giữ nhãn trước phân xử, confusion table, tỷ lệ mơ hồ và lý do phân xử. Agreement
không đồng nghĩa validity. Báo raw agreement và thước đo chance-corrected phù hợp
với kiểu nhãn; xem ảnh hưởng prevalence, không lấy một ngưỡng kappa tùy ý làm bằng
chứng duy nhất. Nguồn phương pháp: [Artstein & Poesio, CL 2008](https://aclanthology.org/J08-4004/).

Nguồn truyện/cụm can thiệp là đơn vị lấy mẫu; không coi từng câu, từng predicate
hoặc hai biến thể cùng truyện là độc lập. So sánh hai model phải resample cùng
source cho cả hai rồi tính hiệu số; báo từng seed và biến thiên do seed riêng.
Không dùng số lượng nhiều sentence để tạo CI nhỏ giả. Tham khảo nguyên tắc lựa
chọn kiểm định trong [Dror et al., ACL 2018](https://aclanthology.org/P18-1128/).

Minh họa **độ chính xác ước lượng, không phải power analysis**: với Bernoulli độc
lập ở trường hợp xấu nhất p=0.5, \(n\approx1.96^2(0.25)/e^2\): khoảng 97 đơn vị
cho half-width 10 điểm phần trăm; 385 cho 5 điểm. Dữ liệu có cluster, seed và
paired contrast cần mô phỏng dựa trên validation; không bê nguyên hai số này làm
sample-size cuối. Phải ghi trước smallest effect of interest và ngân sách nhãn.

Ví dụ chi phí nhãn: 50 nguồn × 2 tiền đề × 4 model × 3 seed = 1.200 output. Hai
người đọc, mỗi output 3–5 phút/người ⇒ **120–200 giờ-người**, chưa tính hướng dẫn
và phân xử. Đây là giả định để lập ngân sách, **chưa đo**. Chọn mẫu phân tầng được
định trước để giảm chi phí, không chỉ chấm những output đẹp hoặc dễ.

## 11. Dữ liệu, tài nguyên và giới hạn bài

TinyStories dùng để học/đo tiếng Anh nói chung; không thay cho natural evaluation
hay gold logic. Dataset card chính thức đang ghi **CDLA-Sharing-1.0**:
[nguồn](https://huggingface.co/datasets/roneneldan/TinyStories).
Lưu version, giấy phép và nghĩa vụ phân phối; giấy phép của PDF không tự là giấy
phép dataset. Truyện tự viết phải ghi tác giả/đồng ý; không dùng thông tin nhạy cảm.
Truyện naturalistic tạo bằng template phải công bố đúng nguồn gốc. Với truyện
tự nhiên, mọi invariant phải được thẩm định; không áp closed-world tùy tiện.

Máy đã xác minh là RTX 5050 Laptop, 8.151 MiB VRAM theo nvidia-smi, không phải RTX
3060. Calibration MIM trước đây: 20.306 targets / 39,84 giây train, khoảng
509,72 targets/s trên corpus smoke rất nhỏ. Ngoại suy 120M tại tốc độ ấy là khoảng
65,4 giờ train; **không phải dự báo thực tế**: độ dài, pipeline dữ liệu, validation,
generation, chọn siêu tham số và tải nhiệt chưa được tính. Phải đo lại từng hệ.

Tính \(H=\sum_r N_r/(3600v_r)\), trong đó \(N_r\) là target tokens thực và \(v_r\)
là throughput đo đúng cấu hình của run r. Colab throughput, compute-unit burn và
tổng giá tiền hiện **chưa đo**. Không có cơ sở bảo đảm một gói $50 sẽ đủ. Q3-A có
thể ưu tiên inference/validation thay vì train lại cả matrix nếu câu hỏi phép đo
được trả lời tốt hơn; phải sửa protocol trước test và giải thích rõ.

Journal trong kế hoạch trước: J.UCS nếu đóng góp đánh giá có ích cho CS; Journal
of Language Modelling nếu có phát hiện ngôn ngữ học đủ sâu. Chưa xác minh lại toàn
bộ phí/hạng/UEH trong lượt này; không coi đó là journal Q3 đã chốt hay tài trợ đã
được duyệt. Xem [khảo sát trước](PUBLICATION_PLAN.vi.md), kiểm tra lại trước nộp.
Không chọn loại bài để lách điều kiện tài trợ, không thêm đồng tác giả danh nghĩa.

## 12. Những gì có thể viết ngay và bằng chứng còn thiếu

| Phần bản thảo | Có thể viết ngay | Phần phải để trống đến khi có bằng chứng |
|---|---|---|
| Introduction | Vấn đề đánh giá probe→generation; khoảng trống có điều kiện. | Claim mạnh nhất, effect size, lời hứa “first”. |
| Related work | Ma trận trên; phân biệt revision, tracking, evaluation và architecture. | Khẳng định bao phủ toàn bộ literature. |
| Formal task & data | Ngữ nghĩa, schema, luật, split, annotation protocol sau validation. | Số lượng cuối, agreement, natural transfer chưa thu. |
| Evaluation | Primary/secondary, evasion, paired/no-op, đơn vị cluster. | Kết luận metric có validity trước validation. |
| Experiments | Hệ so sánh, actual parameter counts, ngân sách chọn cấu hình. | Bảng thắng/thua, GPU-giờ, seed results chưa chạy. |
| Results & discussion | Khung câu hỏi và loại sai; quy tắc chọn ví dụ. | Số liệu, kiểm định và giải thích nhân quả chưa chứng minh. |
| Limitations/ethics | Ngôn ngữ, phạm vi mô phỏng, người chấm, tài nguyên. | Funding, acceptance, submission chưa xảy ra. |

Bộ hình/bảng quyết định: (1) ma trận độ mới; (2) errors theo depth tại fixed
length và theo length tại fixed depth; (3) probe×generation 2×2; (4) changed vs
preserved, kèm no-op; (5) self-event creation vs unconditional consistency;
(6) agreement/confusion và ngân sách. Không cần đủ mọi hình nếu chúng không hỗ
trợ claim cuối; không làm nhiều thí nghiệm chỉ để có thêm bảng.

Trước buổi gặp giảng viên nên có: một trang câu hỏi/đóng góp, ma trận 6–9 bài gần,
12 cặp development có giải thích nhãn minh họa, rubric, kế hoạch người chấm và
ngân sách. Mẫu do người nghiên cứu tự soạn phải ghi đúng nguồn gốc, không gọi là
nhãn độc lập đã thu.

## 13. Lộ trình chuẩn bị 4 tuần — có điều kiện hoàn thành

1. **Tuần 1:** chốt task contract và novelty matrix; 12–24 cặp development,
   cả effective/no-op; chạy mẹo đơn giản. Hoàn thành khi không còn trường hợp
   hai cách diễn giải hợp lý cho một “gold” bắt buộc mà rubric không xử lý.
2. **Tuần 2:** hai người đọc thử độc lập; một reference có khả năng viết; audit
   metric trên lỗi chủ đích và lỗi tự nhiên. Hoàn thành khi xác định được lỗi
   người/metric, quy tắc mơ hồ, chi phí nhãn và thiết kế khắc phục shortcut.
3. **Tuần 3:** triển khai schema v1 và CI paired còn thiếu; freeze protocol,
   nguồn/license, test/hash và budget. Hoàn thành khi có reproducible development
   report và xác định được precision/sample size phù hợp ngân sách.
4. **Tuần 4:** chạy pilot được phép theo protocol và viết Methods/Related Work;
   chỉ viết kết quả từ log thật. Có dự phòng sửa lỗi; một tháng không bảo đảm có
   bài đủ bằng chứng, nộp được hay được chấp nhận.

**Thí nghiệm rẻ nhất làm lung lay đề tài:** đặt cạnh nhau probe và continuation
trên bộ development đã chống last-recipient/clock-only; có no-op và output tự
sinh; dùng một reference biết viết và hai người đọc. Nếu không thấy chẩn đoán
thêm ngoài lỗi format/fluency, hoặc chính người chấm không thống nhất được “đúng”,
hãy thu hẹp/sửa phép đo trước khi chi GPU-giờ. Nếu sau validation phần mới vẫn chỉ
là đổi template, gộp thành phần đánh giá của Q1 hoặc dừng Q3-A độc lập. Đây không
phải chạy lại seed đến khi có kết quả thuận chiều.

Xem [10 câu hỏi phản biện và cách trả lời](Q3_A_ADVISOR_QA.vi.md).
