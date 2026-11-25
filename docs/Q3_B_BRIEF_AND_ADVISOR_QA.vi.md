# Q3-B — nhiệm vụ, phương pháp và 10 câu hỏi khó

**Title:** *Tokens or State Changes? A Controlled Study of Delayed Supervision
for Compact Language Models*.

**Nhiệm vụ mục tiêu.** Theo dõi vị trí mới nhất của một vật qua event stream,
rồi viết tiếp 3–5 câu nêu vị trí tại điểm cắt và giải thích vì sao deliveries
của vật khác không thay đổi nó. QA một nhãn vị trí chỉ là component probe.

**Methodology.** B0: probe ngay sau evidence; B1: delay 256 byte-tokens, zero
intervening writes; B2: cùng delay, sáu state-changing writes trên vật khác;
B3: mixture khóa trước. Mỗi source chứa cả low/high windows, thứ tự được
counterbalance; raw event LM corpus giống nhau giữa arm. Câu trả lời đúng và
số answer targets khớp theo source. QA dùng prefix bị cắt tại probe, trên nhánh
riêng; answer không được đưa trở lại event stream. Loss là
`L_event + 0.25 L_answer`, mỗi thành phần là CE mean; trần 2M **tổng CE targets**
/run tính cả event và answer. Primary B2−B1 trên continuation success. Test
cross lag 256/384 và write load 0/3/6; báo probe accuracy riêng, nguồn/seed/chi
phí riêng, không nhận đây là tác dụng thuần của thời gian.

Tiền lệ gần: [Delayed Supervision](https://arxiv.org/abs/2609.32312), preprint,
đã dùng simulator-grounded delayed QA và disposable branches. Phần còn lại
cần chứng minh là kiểm soát delay/write/format/compute và chuyển sang generation.

## 1. Đây có phải chỉ tái làm Delayed Supervision ở model nhỏ?

Nếu chỉ thêm probe trễ rồi thấy QA tăng thì đúng là chưa đủ. B tách token
distance khỏi semantic writes, giữ answer labels/format và event corpus, rồi
đo generation transfer. Cần insight hoặc kết quả âm đủ chính xác về confound,
không lấy thêm seed hay đổi backbone làm novelty.

## 2. Token delay và semantic write khác nhau ở đâu?

Token delay là số token sau evidence đến probe; ở pilot tokenizer byte khiến
đo chính xác bằng số byte ASCII. Write là một lần vị trí của vật thật sự đổi.
Low block chứa câu đệm không cập nhật fact; high block có sáu cập nhật khác
giá trị cũ, kiểm tra bằng simulator. Đếm câu hay số lần nhắc tên không thay được write count.

## 3. Có thực sự giữ ngang khoảng cách và vị trí tuyệt đối không?

B1/B2 cùng lag, còn prefix trước window có thể dài khác. Thứ tự low/high được
counterbalance để giảm confound vị trí; prefix replay/gradient span vẫn phải
đo và công khai. Thiết kế không biện minh cho một claim causal thuần nếu nội
dung lexical hoặc total prefix cost còn giải thích hiệu ứng.

## 4. Hai arm có học cùng event corpus không?

Có: cùng raw event text và cùng thứ tự source theo seed. Chỉ probe placement
thay đổi; câu trả lời năm ký tự cộng EOS khớp theo source. Event targets và QA
targets được đếm riêng. Không đưa đáp án probe vào truyện, không reset một arm
ở giữa source trong khi arm khác được giữ context.

## 5. Nếu fact đổi trước probe thì nhãn cũ có sai không?

Evidence được đặt sau lần cập nhật liên quan cuối; target được kiểm tra còn
đúng đến probe. Trong high block chỉ vật khác đổi. Trước evidence có ghi đè
target để buộc dùng latest value. Nếu mở rộng sang revision-after-evidence,
phải đổi nhãn và đo delay từ lần revision mới, không tái dùng nhãn cũ.

## 6. Model có nhìn thấy tương lai khi train QA không?

QA forward chỉ dùng byte prefix đến probe và query. Sửa phần event stream sau
điểm ấy không đổi QA input; causal model checks được chạy riêng. Event LM vẫn
được train bằng next-token prediction trên toàn source như nhau cho mọi arm;
đó là corpus training, không phải cung cấp future tokens trong QA inference.

## 7. Vì sao `L_event + 0.25 L_answer` mà lại tính chung target budget?

Loss weight điều khiển gradient, còn budget đếm vị trí nhãn CE thực được dùng;
đây là hai đại lượng khác nhau. Cả bốn arm có cùng weight và nhãn. Cắt batch
cuối để event+answer targets không vượt cap; log từng phần và mọi prefix replay.
Không coi một answer target là miễn phí chỉ vì ít ký tự.

## 8. Probe tốt hơn có chứng minh model viết nhất quán hơn không?

Không. Primary là đoạn viết đúng mọi mệnh đề bắt buộc, không mâu thuẫn và đúng
format. Probe exact-match là component metric. Nếu chỉ probe tăng nhưng prose
không tăng, kết luận là khoảng cách access-versus-use trong phạm vi đã thử,
không tuyên bố bộ nhớ ngôn ngữ hữu ích hơn.

## 9. Làm sao biết B2 không chỉ được thêm compute?

Đếm processed tokens, probe-prefix lengths, time/VRAM, target counts và selection
budget. B1/B2 bằng token lag chưa bằng total prefix compute. Muốn compute-matched
replication phải chốt cap và báo lượng target còn lại; không trộn hai điều kiện
thành một bảng “công bằng tuyệt đối”. Hiện throughput/CU còn chưa đo.

## 10. Khi nào nên sửa benchmark hoặc dừng bài?

Nhãn không giữ hiệu lực; write counts sai; shortcut vị trí/wording giải thích
hết; task chỉ là đọc token vừa nhắc; hoặc hiệu ứng không chuyển sang prose
giữ riêng. CI resample source, không resample câu; báo mỗi seed và negative
results. Trước full run còn cần đánh giá tự nhiên có giấy phép/human review;
source integrity hoặc finite gradients không chứng minh novelty.


Đính chính vận hành chung 26/11: warm-up thêm 2.792/277/280 ví dụ chỉ dẫn viết
ba câu, tách máy móc từ chính split TinyStories tương ứng. Tổng nguồn gốc vẫn
3.000/300/300; số dòng trộn là 5.792/577/580, không phải số truyện độc lập mới.
Không thêm state labels benchmark, không tăng cap 5M/init. Perplexity chỉ chấm
truyện gốc giữ riêng, loại các dòng chỉ dẫn dẫn xuất. Khả năng viết phải kiểm
tra sau train, không suy ra từ việc đã thêm format examples.
