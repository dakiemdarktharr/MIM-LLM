# Q3-A — 10 câu hỏi khó và câu trả lời để bảo vệ đề cương

Ngày: **25/11/2026**. Các câu trả lời dưới đây là lời đáp mẫu cho giai đoạn đề
cương. “Em sẽ” là công việc đề xuất; không đổi thành “em đã” khi chưa có log thật.
Xem [hồ sơ nghiên cứu](Q3_A_RESEARCH_DOSSIER.vi.md) và
[sổ nguồn](Q3_A_SOURCE_LEDGER.vi.md) để kiểm tra phạm vi bằng chứng.

## 1. TIME TRAVEL, PASTA và ConStory-Bench đã có cả rồi. Chính xác em còn mới ở đâu?

**Cách trả lời:** “Em không nhận phản thực tế, invariant hay kiểm tra truyện tự
sinh là mới. TIME TRAVEL đã có causal invariance; PASTA đã có state-conditioned
revision; ConStory-Bench đã kiểm tra mâu thuẫn với lịch sử sinh. ChronoScope cũng
đã chỉ ra single-turn accuracy không đủ cho temporal coherence. Phần em muốn kiểm
tra là **giá trị chẩn đoán tăng thêm** của một protocol tiếp nối 3–5 câu, có quy
tắc áp dụng ở thời điểm xác định, cập nhật thật và can thiệp effective/no-op,
khi đã giữ tương đương độ dài và thông tin. Em phải chỉ ra loại lỗi và đối chứng
mà cách chấm trước chưa phân biệt trong cùng điều kiện. Khác độ dài hay ghép các
yếu tố đã biết chưa đủ. Nếu không chứng minh được, em sẽ gộp phần này vào Q1.”

**Bằng chứng phải mang theo:** ma trận task/input/output/metric/control của
[TIME TRAVEL](https://aclanthology.org/D19-1509/),
[PASTA](https://aclanthology.org/2023.tacl-1.73/),
[ConStory-Bench](https://aclanthology.org/2026.findings-acl.410/) và
[ChronoScope](https://aclanthology.org/2026.acl-long.2133/); một cặp mà metric có
sẵn và protocol đề xuất cho chẩn đoán khác nhau, sau đó kiểm chứng trên nhiều nguồn.

**Không được nói:** “Chưa ai đánh giá mô hình nhớ điều chính nó viết” hoặc “đây
là benchmark đầu tiên về counterfactual invariance”.

## 2. Câu hỏi khoa học là gì? Nếu MIM thua thì bài Q3-A còn gì?

**Cách trả lời:** “Q3-A nghiên cứu phép đo, không chứng minh MIM tốt hơn. Giả
thuyết của em là số cập nhật còn liên quan và phạm vi điều kiện làm xuất hiện lỗi
trong đoạn sinh, vượt lỗi ở probe một dữ kiện, sau khi kiểm soát độ dài và khả
năng viết. Giả thuyết đối nghịch là chất lượng ngôn ngữ/làm theo hướng dẫn đã giải
thích hết, protocol mới không thêm thông tin. Kết quả âm có ích nếu phép đo đáng
tin và ước lượng đủ rõ; một benchmark mới mà chỉ cho biết mọi mô hình nhỏ đều
viết kém thì chưa đủ bài. MIM thắng hay thua sẽ được báo nguyên trạng.”

**Bằng chứng phải mang theo:** một primary metric và contrast xác định trước;
bảng 2×2 probe/continuation; effect theo depth ở fixed length và theo length ở
fixed depth; CI và giả thuyết thay thế. Claim kiến trúc để riêng cho Q1.

**Không được nói:** “Chỉ cần MIM đạt điểm cao hơn là benchmark có validity.”

## 3. Tại sao em biết tủ phải mở lúc 9 giờ? ‘Phải làm’ có chắc đã làm không?

**Cách trả lời:** “Không chắc nếu chỉ có nghĩa vụ. Em cần ghi rõ thế giới thí
nghiệm có nhân vật tuân thủ quy tắc, giao chìa thành công trước 9 giờ, không có
đường mở khác, và tủ khóa ngay trước hành động. Quy tắc đúng 9 giờ được kiểm tra
một lần. Điện 8:55 thì Mai mở tại 9:00; điện 9:05 thì tại 9:00 Mai chờ và tủ
khóa. Em không tự suy ra mở lúc 9:05 nếu chưa có luật mở khi điện trở lại.
Trạng thái có chỉ số thế giới, thời điểm và thứ tự sự kiện; Mai giữ chìa trước
khi mở, nhưng có thể đặt nó xuống sau đó. Em đang đo thực hiện một microworld
đã đặc tả, không khẳng định suy ra nhân quả đời thực.”

**Bằng chứng phải mang theo:** task contract, event ledger trước/sau quyết định,
oracle độc lập với cách diễn đạt; ví dụ boundary 9:00 bị loại hoặc có tie order.
Phân biệt possession với ownership. Counterfactual của prefix 9:05 “muộn hơn
mười phút” phải là 9:15.

**Không được nói:** “Hễ có từ ‘must’ thì sự kiện chắc chắn xảy ra.”

## 4. Mỗi mô hình viết một đoạn khác nhau. Em lấy đâu ra đáp án đúng để chấm?

**Cách trả lời:** “Em không dùng một reference duy nhất. Gold gồm tập mệnh đề
bắt buộc có chỉ số thế giới/thời điểm; phần sáng tác tự do có nhiều đáp án đúng.
Đoạn nào đặt chìa ở ngăn kéo thì phần sau phải tôn trọng ngăn kéo; đoạn đặt chìa
ở túi áo được chấm theo túi áo. Oracle chỉ xác định hệ quả trong event model;
diễn giải lời văn vẫn cần rubric và kiểm tra người đọc. Em tách thiếu mệnh đề,
mơ hồ, mâu thuẫn và sai format. Không nhắc một điều không đồng nghĩa phủ nhận nó.”

**Bằng chứng phải mang theo:** ba đoạn hợp lệ khác nhau cho cùng prefix; các cặp
tối thiểu chỉ sai một điều; span bằng chứng cho từng nhãn; semantic-only score
bên cạnh primary 3–5 câu. [TRIP](https://aclanthology.org/2021.findings-emnlp.422/)
và [FactTrack](https://aclanthology.org/2025.naacl-long.144/) là tiền lệ liên kết
mâu thuẫn với trạng thái và hiệu lực theo thời gian, không phải đáp án sinh duy nhất.

**Không được nói:** “Oracle đúng nên bộ chấm free text chắc chắn đúng.”

## 5. Độ sâu ghi đè chỉ làm truyện dài hơn. Làm sao biết em đang đo memory?

**Cách trả lời:** “Phê bình đó đúng với pilot hiện tại nếu dùng nguyên trạng.
Em phải biến thiên số cập nhật liên quan ở độ dài tương đương, và biến thiên độ
dài khi giữ số cập nhật. Em cũng kiểm soát recency, số vật và vị trí câu quyết
định. Mã v0 luôn lấy người nhận cuối; nó chưa chống được heuristic. Em sẽ thêm
quay lại người cũ, người nhắc cuối không liên quan, giao vật khác và chuyển thất
bại có ngữ nghĩa rõ; giữ họ template ngoài train. Chỉ đổi tên không chứng minh
khái quát hóa. Nếu depth effect mất sau kiểm soát, phải báo đúng kết quả đó.”

**Bằng chứng phải mang theo:** kết quả last-recipient, last-mentioned, clock-only,
always-open/wait và copy/no-change; bảng matching độ dài/recency; source/template
split audit. [Naturalistic entity tracking 2026](https://aclanthology.org/2026.emnlp-main.2231/)
đã xem recency nên đây là kiểm soát cần kế thừa, không phải phát minh mới.

**Không được nói:** “Truyện dài hơn làm sai nhiều hơn, vậy chắc chắn bộ nhớ kém.”

## 6. Mô hình có thể tránh sai bằng cách nói chung chung. Và đọc lại output có phải chứng minh bộ nhớ nội tại?

**Cách trả lời:** “Không. Em báo cả coverage và khả năng tạo sự kiện mới làm đổi
trạng thái, không chỉ ít mâu thuẫn. Với self-event, cố định nguyên văn/token IDs
đoạn đầu, ghi sự kiện thực tế nó chọn, rồi chấm phần tiếp theo theo lịch sử ấy.
Em báo tỷ lệ tạo sự kiện, nhất quán trong nhóm có sự kiện và thành công vô điều
kiện. Không tạo sự kiện không được credit là nhớ đúng. Nếu đoạn đầu đã sai prefix
thì tự nhất quán về sau không xóa lỗi đầu. Khi toàn lịch sử vẫn nằm trong prompt,
thí nghiệm chỉ chứng minh hành vi dùng ngữ cảnh; không chứng minh recurrent hidden
state là nơi lưu thông tin.”

**Bằng chứng phải mang theo:** ví dụ né lỗi, ví dụ sự kiện mới không nằm trong
prefix, nhãn state có hiệu lực, log phần prefix/generation đóng băng. Tách nhóm
backbone thuần và controller ngoài như
[ConWriter](https://aclanthology.org/2026.findings-emnlp.359/).

**Không được nói:** “Tỷ lệ mâu thuẫn 0% nghĩa là mô hình nhớ hoàn hảo.”

## 7. Mô hình hai triệu tham số viết chưa được. Em có đang nhầm lỗi ngôn ngữ với lỗi logic?

**Cách trả lời:** “Có nguy cơ đó. Bản MIM-LM BPE-512 hiện có 2,081,472 tham số;
10M targets/run là ngân sách pilot, chưa bảo đảm fluency. Em đo PPL trên văn bản
giữ riêng, format, độ trôi chảy và logic tách biệt. Dùng cùng câu chuyện cho probe
và continuation nhưng chạy riêng, không tiết lộ probe answer. Thêm một model mở
biết viết làm capability reference để kiểm tra benchmark có đo được điều gì vượt
writing floor không. Nó không phải đối chứng khớp tài nguyên với MIM. Nếu mọi
model chỉ sinh vụn câu, em phải sửa điều kiện khả năng viết trước kết luận memory.”

**Bằng chứng phải mang theo:** mẫu output lấy theo quy tắc định trước; fluency
blind rating; PPL dưới cùng tokenizer cho nhóm train tương đương; reference có
model/data/decoding card riêng. Không loại output khó chỉ để làm đẹp tỷ lệ logic.

**Không được nói:** “PPL thấp chứng minh đoạn viết đúng quan hệ nhân quả.”

## 8. Ai chấm? Em có kiểm chứng người chấm và LLM judge không?

**Cách trả lời:** “Chưa có nhãn người thật, nên hiện em chưa báo agreement.
Kế hoạch là hai người đọc chấm độc lập, mù tên model, tập trên development;
giữ nhãn trước phân xử và cho phép mơ hồ. Em báo raw agreement, confusion table,
thước đo chance-corrected phù hợp, prevalence và thời gian. Agreement cao không
tự chứng minh nhãn đúng. Nếu dùng judge, em kiểm trên cả lỗi gieo chủ đích lẫn lỗi
sinh tự nhiên, theo loại lỗi, với dẫn chứng văn bản. Không dùng cùng một parser
để tạo gold và tự chứng minh parser đúng.”

**Bằng chứng phải mang theo:** rubric có ví dụ ranh giới; nhãn độc lập và nhãn
phân xử riêng; false-positive/false-negative; log người đọc và consent thực.
Đọc [Artstein & Poesio](https://aclanthology.org/J08-4004/) về agreement và
[OpenMEVA](https://aclanthology.org/2021.acl-long.500/) về validation metric truyện.

**Không được nói:** “Một GPT chấm nên khách quan” hay bịa hai bộ nhãn như người thật.

## 9. Bao nhiêu truyện mới đủ? Vì sao không coi mỗi câu là một mẫu?

**Cách trả lời:** “Các câu trong một truyện và hai nhánh từ cùng nguồn phụ thuộc
nhau. Đơn vị là source story/paired cluster. Em resample cùng source cho các model
khi ước lượng hiệu số, giữ nhánh trong cluster; báo từng seed và biến thiên seed.
Số mẫu chốt từ precision/power cho contrast cụ thể dựa trên validation, không
chọn sau khi thấy test. Ví dụ Bernoulli độc lập cho 95% half-width 5 điểm phần
trăm cần khoảng 385 đơn vị ở p=0.5, nhưng đó không phải power analysis cho thiết
kế paired nhiều seed. Chi phí nhãn thường là ràng buộc lớn hơn GPU.”

**Bằng chứng phải mang theo:** estimand, smallest effect of interest, simulation
sample size, bootstrap paired theo source, kế hoạch so sánh phụ/multiple testing.
Ví dụ 50 nguồn×2 tiền đề×4 model×3 seed, hai người đọc 3–5 phút/output ⇒
120–200 giờ-người; đây là giả định cần đo lại, chưa phải công việc đã làm.
Xem [Dror et al.](https://aclanthology.org/P18-1128/).

**Không được nói:** “Có vài nghìn câu nên CI chắc chắn đáng tin.”

## 10. Một tháng có xong không, nộp đâu, và lúc nào phải dừng thay vì cố ra ba bài?

**Cách trả lời:** “Một tháng có thể là mốc hoàn thành feasibility và Methods,
không bảo đảm đủ bài hay được nhận. Em ưu tiên ngữ nghĩa, chống shortcut và nhãn
trước grid search. Máy hiện là RTX 5050 Laptop khoảng 8 GB; Colab tốc độ và CU chưa
đo, nên em chưa thể hứa $50 cover train. J.UCS là ứng viên trong kế hoạch nếu có
đóng góp CS; JLM cần insight ngôn ngữ học và kiểm tra đúng ngành quartile. Phí,
hạng và UEH phải xác minh lại, chưa có tài trợ hay chấp nhận. Nếu không có giá trị
chẩn đoán thêm, nhãn không đáng tin, hoặc chỉ đổi template, em gộp/dừng Q3-A.
Q3-B về supervision, Q3-C về mechanism, Q1 về kiến trúc cần đóng góp riêng và công
khai phần dùng chung; không xé cùng một kết quả thành bốn bài.”

**Bằng chứng phải mang theo:** milestone theo tuần có completion gate, dự toán
nhãn/GPU từ đo thật, bảng overlap bốn bài, stop/merge rule. Kiểm tra kế hoạch
journal/UEH ở [PUBLICATION_PLAN.vi.md](PUBLICATION_PLAN.vi.md); lượt nghiên cứu này
không phải lần tái xác minh phí/hạng. Giữ riêng drafted/submitted/accepted/published.

**Không được nói:** “Q3 dễ nên mỗi tháng chắc chắn có một bài”, hoặc thêm giảng
viên không có đóng góp để hợp thức hóa tài trợ.

## Cách dùng trước buổi gặp

Tập trả lời mỗi câu khoảng 60–90 giây, sau đó mở đúng bảng/nguồn minh chứng.
Điều chưa biết nên trả lời “em chưa đo; đây là phép kiểm tra để xác định”, kèm
tiêu chí quyết định. Với đề cương hiện tại, ba điểm cần xin góp ý chuyên môn nhất
là mức đóng góp độc lập của Q3-A, tính chặt chẽ của task contract và ngân sách
người chấm. Không biến phần trả lời mẫu này thành bằng chứng thực nghiệm.
