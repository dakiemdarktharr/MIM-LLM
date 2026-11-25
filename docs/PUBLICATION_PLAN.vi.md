# MIM-LLM: đề tài, journal, tài trợ UEH và dự toán
Ngày khảo sát: **25/11/2026**, múi giờ Việt Nam. Đây là thiết kế dự kiến; không phải bốn bài đã có kết quả. Bạn xác nhận là **sinh viên UEH, chưa có giảng viên đồng tác giả**.

## Bốn câu hỏi độc lập

| Bài | Tiêu đề làm việc | Mục tiêu và câu hỏi chính | Đóng góp cần chứng minh | Journal dự kiến |
| --- | --- | --- | --- | --- |
| Q3-A | Temporal Conditions, State Overwrites, and Counterfactual Invariance in Autoregressive Story Continuation | Đo việc mô hình giữ đúng phạm vi thời gian của điều kiện sau nhiều lần thay đổi trạng thái. Đổi một tiền đề làm đổi hệ quả nào, giữ dữ kiện nào? | Phương pháp chấm cùng phát hiện thực nghiệm về tương tác giữa ghi đè, thời gian và hai thế giới; không chỉ phát hành dữ liệu. | **J.UCS**; JLM chỉ khi có phát hiện ngôn ngữ học đủ sâu và chấp nhận Q3 ngành Linguistics. |
| Q3-B | Training-Only State Supervision for Consistent Short Story Continuation | Nhãn trạng thái khi train có giúp cùng backbone viết ít mâu thuẫn hơn trên truyện mới, khi inference không có bảng trạng thái? | Hiệu ứng của thông tin giám sát, khả năng chuyển miền và chi phí nhãn; tách khỏi đổi kiến trúc. | **Inteligencia Artificial**, tạm thời vì hạng cần xác minh trực tiếp; **J.UCS** dự phòng. |
| Q3-C | Which Recurrent Memories Matter? A Controlled Study of Vector MIM for Story Continuation | N, S, M đóng góp gì trên mỗi tham số và mỗi giờ GPU? Có còn ích khi đối chứng nhìn cả hai trạng thái? | Phát hiện về cơ chế/hiệu quả và phạm vi thất bại, có thể là kết quả âm. | **J.UCS**; Inteligencia Artificial dự phòng có điều kiện. |
| Q1 | Explicit State Differences and Nested Memory for Consistent Autoregressive Story Continuation | Buộc dùng sai phân qua MIM-N → MIM-S có cải thiện tổng quát trên truyện tự nhiên, hai tình huống và sự kiện tự sinh? | Bằng chứng kiến trúc vượt đối chứng trộn hai trạng thái, nhiều seed và miền, có chi phí và chất lượng viết. | **TACL**; **JMLR** chỉ khi phát hiện có giá trị rộng cho ML, không phải phương án dễ hơn. |

Q3/Q1 là **mục tiêu chọn nơi nộp**. Quartile phụ thuộc năm, hệ xếp hạng và ngành; quyết định phản biện chưa thể biết trước. Q1 có thể nộp ngay khi đủ bằng chứng. Q3-C phải gộp vào Q1 nếu chỉ là bảng ablation của bài chính.

## Bảng phác thảo chi tiết ba bài Q3

| Hạng mục | Q3-A: đo lường/ngữ nghĩa | Q3-B: giám sát trạng thái | Q3-C: cơ chế bộ nhớ |
| --- | --- | --- | --- |
| Đơn vị dữ liệu | Truyện nguồn + cặp tiền đề; không lấy mỗi câu làm mẫu độc lập | Cùng corpus, thêm nhãn trạng thái ở train | Cùng corpus/tokenizer và benchmark đã khóa |
| Dữ liệu | TinyStories cho viết nói chung; synthetic có oracle; truyện tự viết hoặc cấp phép, người đọc tại Việt Nam | Cùng dữ liệu ngôn ngữ; nhãn train đã kiểm tra; test khác truyện và dạng quy tắc | Cùng dữ liệu ngôn ngữ và test; không dùng trạng thái chuẩn lúc inference |
| Core matrix dự kiến | LSTM, Transformer, MIM, learned-pair × 3 seed | MIM/LSTM × có/không auxiliary state loss × 3 seed | MIM, no-N, no-S, no-M, learned-pair, Delta-RNN, Nested LSTM, minGRU × 3 seed |
| Thông tin quan trọng | Cặp chỉ sửa một span; tách mệnh đề buộc đổi/giữ/tuỳ chọn | Giữ head có cùng kích thước ở arm đối chứng; báo tổng và tham số thực sự cập nhật | Learned-pair có thể học chính phép trừ; phải nhìn cả hai vector |
| Chỉ số chính | Đoạn 3–5 câu đủ mệnh đề bắt buộc và không mâu thuẫn | Chênh lệch chỉ số chính khi bật/tắt state loss ở cùng backbone | Chênh lệch của từng memory path ở khớp tham số; báo thêm khớp chi phí |
| Chỉ số phụ | Hệ quả đổi, invariant, phạm vi điều kiện, self-event, độ phủ, fluency, PPL | Như A; thêm state-probe, lỗi nhãn và chuyển miền | Như A; thêm throughput, VRAM, GPU-giờ và độ ổn định seed |
| Hình quyết định | Lỗi theo độ sâu ghi đè × dạng điều kiện; độ đúng hệ quả đổi so với invariant | Hiệu ứng có/không nhãn theo nguồn truyện và độ sâu | Consistency theo GPU-giờ; hiệu ứng bỏ N/S/M |
| Bảng quyết định | Số nguồn, giấy phép, đồng thuận trước phân xử, metric theo seed | 4 arm; tham số/head, tokens, compute, interval | 8 arm; tham số/gap, metric, fluency, compute |
| Điều kiện viết | Nhiều dạng hiện tượng; test tự nhiên; chấm đáng tin; có phát hiện khoa học | Hiệu ứng ổn định hoặc kết quả âm giải thích được; không chỉ học grammar của nhãn | Có kết luận cơ chế độc lập, khớp thông tin và công bố sai lệch tài nguyên |
| Gộp/dừng | Chỉ một mẫu tủ; dữ liệu/nhãn không đáng tin; chỉ còn bài dữ liệu | Chỉ một head phụ không tạo hiểu biết mới | Trùng câu hỏi/bảng kết quả Q1 hoặc hiệu ứng do tài nguyên |
| Tệp LaTeX | papers/q3_a_temporal_benchmark/main.tex | papers/q3_b_state_supervision/main.tex | papers/q3_c_memory_mechanisms/main.tex |

**Ablation** là phép bỏ/thay một thành phần để xem điều gì thay đổi. **Seed** là khởi tạo ngẫu nhiên khác; phải báo từng seed. **Invariant** là dữ kiện vẫn đúng sau khi đổi một tiền đề. Với self-event, trạng thái sau đoạn đầu do mô hình tự viết mới là lịch sử dùng để chấm đoạn sau.

Mã hiện có là nguyên mẫu, không thực hiện sẵn toàn bộ nghiên cứu: benchmark hiện có một họ quy tắc tủ và độ sâu 2–5; state head hiện có một nhãn phân loại/token. Nhiều loại quy tắc, nhãn nhiều thuộc tính/hai thế giới, can thiệp bộ nhớ và test truyện tự nhiên vẫn cần triển khai/kiểm tra theo dữ liệu thực. Đừng gọi những phần này là thí nghiệm đã xong.

## UEH: điều kiện hiện tại và mức tiền có thể xét

[Q&A chính thức UEH](https://hotro.ueh.edu.vn/bai-viet/q-a-vien-chuc-nguoi-lao-dong-11833), mục 55, yêu cầu người học có đồng tác giả là viên chức UEH; viên chức đại diện đăng ký. Với tình trạng bạn đã xác nhận, **chưa đủ điều kiện xét**. Người tham gia phải có đóng góp thực chất; không thêm tên chỉ để xin tiền.

[Hướng dẫn 491, hiệu lực 01/04/2025](https://rdge.ueh.edu.vn/wp-content/uploads/2025/05/491-Huong-dan-tai-tro-va-thuong-bai-bao-CBQT.pdf) loại trừ data paper và dữ liệu sơ cấp thu thập ngoài Việt Nam; phân biệt JCR với Scopus. Trần trước điều chỉnh:

| Nhóm trong văn bản | Tài trợ tối đa | Thưởng tối đa |
| --- | ---: | ---: |
| SSCI/SCIE Q1 | 200 triệu | 100 triệu |
| SSCI/SCIE Q3 hoặc Scopus Q1 | 100 triệu | 50 triệu |
| Scopus Q3 | 60 triệu | 30 triệu |

Mức thực nhận còn phụ thuộc nhà xuất bản (nhóm khác có hệ số 80%), tỷ lệ tác giả/affiliation UEH và phê duyệt. Không mặc định SJR Q3 được áp đúng dòng Scopus Q3. Không cộng tài trợ và thưởng thành tiền chắc chắn.

[Quy trình UEH NCPTGKTC.QT.06, hiệu lực 22/07/2025](https://rdge.ueh.edu.vn/wp-content/uploads/2025/12/Quy-trinh-quan-ly-de-tai-cong-bo-quoc-te-va-thanh-toan-moi.pdf) yêu cầu đăng ký, duyệt, hợp đồng, kê khai sản phẩm và thanh toán. Hướng dẫn 491 nêu thanh toán sau xuất bản online có DOI; đây không phải bảo đảm ứng trước APC. Ngân sách cá nhân tiếp tục tính **0 VND tiền xuất bản**, chưa ghi nhận tài trợ được duyệt.

Chưa tìm thấy văn bản công khai thay thế 491 trong phạm vi tra cứu nêu cuối tệp. Cần giảng viên xác nhận loại bài, ngành, cách lấy Scopus quartile và điều kiện corpus/nhãn người đọc với Ban NC-PT&GKTC trước khi đăng ký. Không chèn lời cảm ơn đã nhận tài trợ trong các khung bản thảo.

## Journal: bằng chứng và giới hạn

| Tạp chí, ISSN, nhà xuất bản | Phù hợp | SJR 2025 (SCImago) | JCR-JIF, tách riêng | Phí bắt buộc | Trạng thái tại ngày tra |
| --- | --- | --- | --- | --- | --- |
| Journal of Universal Computer Science; 0948-695X / 0948-6968; Graz University of Technology, nền tảng ARPHA/Pensoft | A, C; B dự phòng | 0.308; Q3 Computer Science (miscellaneous), Q4 Theoretical Computer Science [S1] | Trang journal hiển thị JIF 1, Q3 Theory & Methods, Q4 Software Engineering; không ghi rõ năm JIF ở chỗ này. Chưa truy cập trực tiếp bảng JCR Clarivate. | Chính sách miễn phí cho tác giả và người đọc [J1] | **Đã xác minh cả phí và hạng (SJR)**; tuyến UEH/JCR cần xác nhận; Scopus trực tiếp bị 403. |
| Journal of Language Modelling; 2299-8470 / 2299-856X; Institute of Computer Science, Polish Academy of Sciences | A chỉ khi có insight ngữ nghĩa/ngôn ngữ học | 0.155; Q3 Linguistics and Language, **Q4 Computer Science Applications**, Q4 Modeling and Simulation [S2] | Chưa xác minh JCR-JIF; không lấy số “impact factor” ở site tổng hợp | Miễn phí tác giả/người đọc [J2]; bản in theo yêu cầu là tùy chọn | **Đã xác minh cả phí và hạng (SJR)**; không chốt là Q3 CS; UEH Scopus quartile chưa rõ. |
| Inteligencia Artificial; 1137-3601 / 1988-3064; IBERAMIA | B; C dự phòng | Nguồn thứ cấp ghi 0.302 Q3 AI/Software; SCImago trực tiếp [S3] bị 403, chưa xác minh đủ | Trang journal tự công bố 2025 JIF 0.9 Q4, ESCI, có chú thích lỗi tên; không chuyển thành SCIE Q3 [J3m] | Không phí nộp, review, APC, xuất bản, editing; đóng góp tự nguyện không bắt buộc [J3] | **Chưa đủ căn cứ** cho hạng trực tiếp/active index và mức UEH, dù chính sách phí rõ. |
| Transactions of the Association for Computational Linguistics; 2307-387X; ACL, MIT Press | Q1 chính | 2.144; Q1 Artificial Intelligence và Computer Science Applications [S4] | Chưa xác minh trực tiếp JCR-JIF Clarivate; không đồng nhất SJR Q1 với JCR Q1 | MIT Press liệt kê Diamond OA (không APC) [J4] | **Đã xác minh cả phí và hạng (SJR)**; chưa xác nhận toàn bộ phí phụ và điều kiện UEH. |
| Journal of Machine Learning Research; 1532-4435 / 1533-7928; JMLR, Inc.; bản in Microtome | Q1 nếu kết quả có giá trị ML rộng | 1.997; Q1, trong đó AI/Software [S5] | Chưa xác minh trực tiếp JCR-JIF | Hướng dẫn tác giả xác nhận không phí xuất bản [J5] | **Đã xác minh cả phí và hạng (SJR)**; tuyến UEH/JCR cần kiểm lại. |

Không có dòng nào ở đây là “UEH đã đồng ý cấp tiền cho bạn”. Chính sách chung không phải danh sách phê duyệt cá nhân. Bằng chứng miễn phí dựa trên tuyên bố tác giả của journal; kiểm lại phí nộp, APC, quá trang, màu bắt buộc, membership và mọi dịch vụ bắt buộc ở lúc nộp. Không dựa vào waiver chưa được duyệt.

| Journal | Review/độ dài và bài gần phạm vi |
| --- | --- |
| J.UCS | Single blind, ít nhất hai thành viên editorial board theo trang journal. Hướng dẫn độ dài chưa truy cập được do 403; chưa chốt số trang. Gần phạm vi: “Insights into Low-Resource Language Modelling…” (2024), DOI 10.3897/jucs.118889; “Enhancing Knowledge Graph Construction…” (2025), DOI 10.3897/jucs.137103. |
| JLM | Ít nhất ba reviewer; yêu cầu linguistic insight, bài phát triển LM đơn thuần ngoài phạm vi. Chưa chốt giới hạn trang. Ví dụ: “Large language models as proxies for theories of human linguistic cognition”, bản accepted/to appear trên site journal [P1]. |
| Inteligencia Artificial | Double blind, ít nhất hai reviewer. Nộp theo template journal; chưa xác minh trần trang regular paper. Ví dụ: “Credit Risk Meets Large Language Models…” (2025), DOI 10.4114/intartif.vol28iss75pp220-247. |
| TACL | AE và ba reviewer; submission theo tháng, có revise/resubmit. Phải dùng template hiện hành và quy tắc appendix; tài liệu cũ 7–10 trang không đủ làm bằng chứng giới hạn hiện tại. Ví dụ: PASTA, TACL 2023 [P2]. |
| JMLR | Editorial screening/AE và phản biện; >35 trang có thể chậm, >50 trang cần giải trình, theo hướng dẫn tác giả. Không thích hợp nếu đóng góp chỉ là ứng dụng hẹp. Ví dụ gần cơ chế: “Memory of recurrent networks: Do we compute it right?”, 2024 [P3]. |

Informatica (Slovenia) được kiểm tra như ứng viên thêm: SJR Q3 nhưng có thông tin thứ cấp mâu thuẫn về Scopus active. **Chưa đưa vào shortlist** khi chưa kiểm tra Sources chính thức. Không đánh đổi tính chắc chắn chỉ để có ba tên journal khác nhau.

## Dự toán train: máy hiện tại và Colab Pro

Hai run hiệu chuẩn ngày 25/11/2026, cùng corpus nhỏ, BPE 512, width 192, context 128, batch 8, seed 0:

| Run | Tham số thực | Tokens thực | Giây train | Token/giây train | Giây toàn run |
| --- | ---: | ---: | ---: | ---: | ---: |
| MIM-LM | 2,081,472 | 20,306 | 39.84 | 509.72 | 45.30 |
| Learned-pair | 2,155,392 | 20,306 | 36.24 | 560.32 | 40.89 |

Đây là hiệu chuẩn ngắn trên 10 truyện TinyStories train đã có, lặp nhiều epoch. **Không dùng loss hay tốc độ của nó làm kết quả khoa học.** Pair nhiều hơn khoảng 3.55% tham số, chưa phải đối chứng khớp chính xác. Run chính phải điều chỉnh width và đo lại context đủ dài, từ vựng/corpus thực, từng kiến trúc và nhiệt độ máy.

Dải dưới đây là **kịch bản dự toán**, không phải khoảng tin cậy đo được:
- Laptop: 250–500 train tokens/s, giảm so với hiệu chuẩn để lập kế hoạch; context/vocab lớn hơn hoặc nhiệt độ máy có thể làm tốc độ thấp hơn dải này.
- Colab Pro: giả sử 500–1,500 train tokens/s; **chưa đo**, có thể chậm hơn dải này.
- Chia 50/50 **số token/run độc lập**, không chia từng câu trong cùng run. Hai nơi chạy song song; thời gian là phía kết thúc muộn hơn. Dải không bao gồm chờ GPU, hết compute units, gián đoạn, validation, generation, chọn siêu tham số hoặc gán nhãn.
- GPU Colab, giới hạn và tài nguyên có thể thay đổi; gói trả phí không bảo đảm luôn có một loại GPU. [FAQ chính thức](https://research.google.com/colaboratory/faq.html). Không mua gói hoặc thêm compute units trong phiên này.

Công thức: H_train = tổng(tokens_run / throughput_run) / 3,600. Với chia 50/50 song song, T = max(0.5N/r_laptop, 0.5N/r_colab)/3,600. Run khác kiến trúc phải dùng tốc độ riêng; bảng dùng một dải chung để thấy bậc chi phí.

| Bài | Core budget đề xuất | Tổng tokens | Chỉ laptop | Chỉ Colab theo giả định | Chia 50/50, chạy song song |
| --- | --- | ---: | ---: | ---: | ---: |
| Q3-A | 4 model × 3 seed × 10M | 120M | 67–133 giờ | 22–67 giờ | 33–67 giờ |
| Q3-B | 2 backbone × 2 arm × 3 seed × 10M | 120M | 67–133 giờ | 22–67 giờ | 33–67 giờ |
| Q3-C | 8 arm × 3 seed × 10M | 240M | 133–267 giờ | 44–133 giờ | 67–133 giờ |
| Q1 core | 7 model × 5 seed × 50M | 1.75B | 972–1,944 giờ | 324–972 giờ | 486–972 giờ |
| Q1 scale extension, có điều kiện | 2 quy mô thêm × 2 model × 5 seed × 50M | +1B | Chưa đo ở quy mô mới | Chưa đo | Chưa đo |

50M/10M là ngân sách đề xuất để kiểm nghiệm, chưa biết có đủ học viết tự nhiên và làm theo yêu cầu. Cần kiểm tra fluency trước khi mở rộng. Q1 có thể vượt xa khả năng dùng máy/Colab nếu tốc độ thực thấp; không hứa Q1 chỉ bằng tăng số tokens.

Dự phòng riêng **20% token-equivalent compute** cho kiểm tra cấu hình/sự cố, khóa trước thay vì grid vô hạn. Validation/generation/annotation phải đo cộng riêng. Nếu chia 50/50 như trên, A tương đương khoảng 4–8 ngày **khi cả hai nơi đều chạy 8 giờ hữu ích/ngày**; C khoảng 8–17 ngày; Q1 khoảng 61–122 ngày. Không đồng nhất các con số này với ngày hoàn tất paper.

Không cộng mù ngân sách của bốn bài: những run trùng corpus, tokenizer, architecture, seed, lịch train, token cap và selection policy có thể tái sử dụng và phải khai báo. Số tokens duy nhất sau loại trùng hiện **chưa chốt**. Tập test/nhãn đã dùng trong bài trước không còn là test “chưa từng nhìn” cho lựa chọn kiến trúc Q1: cần tranche nguồn mới hoặc khóa toàn bộ quyết định trước lần mở test đầu.

## Thời gian làm nghiên cứu, ngoài GPU

| Bài | Thời gian chủ động dự kiến | Phụ thuộc và việc song song |
| --- | --- | --- |
| Q3-A | 3–5 tháng | Ngữ nghĩa, dữ liệu có phép, pilot chấm; pilot MIM/pair chạy song song ngay |
| Q3-B | 3–5 tháng sau khi có schema nhãn | Có thể bắt đầu nhãn và loss khi A còn kiểm tra agreement |
| Q3-C | 3–5 tháng sau khi có benchmark đáng tin | Profile/ablation song song; dành 2–4 tuần sửa implementation |
| Q1 | Tổng chương trình khoảng 18–30 tháng | Dựa trên tín hiệu đầu; không đợi ba Q3 được nhận |

Đây là ước lượng lập kế hoạch cho sinh viên, không phải cam kết lịch của tạp chí. Mỗi bài dự trù thêm 2–6 tuần sửa bản thảo nội bộ và các vòng sửa theo reviewer; **thời gian phản biện chưa biết**.

Công sức người đọc có thể lớn hơn train: mẫu 50 cặp nguồn × 2 điều kiện × 4 model × 3 seed = 1,200 đoạn. Hai người, 3–5 phút/đoạn → khoảng **120–200 giờ-người**, chưa tính huấn luyện rubric, self-event follow-up và phân xử. Đây là phép tính khối lượng, chưa phải số mẫu cuối. Chọn cỡ mẫu từ độ chính xác cần thiết ở cấp truyện, không từ số câu.

## Điều kiện để hoàn tất bản thảo

Có data và bảng kết quả vẫn cần: kiểm định độ tin cậy phép chấm, giải thích hiệu ứng, phân tích âm, đối chiếu nghiên cứu trước, chốt phần mới, giới hạn, authorship, disclosure và đúng template journal. Ba PDF hiện là **khung nghiên cứu**, chưa phải bản thảo có kết quả. Bản thảo / đã nộp / được chấp nhận / xuất bản được theo dõi riêng trong STATUS.md.

## Nguồn và phạm vi tra cứu

Tập nguồn: UEH hotro/rdge và văn bản chính thức; trang author/about/metrics của journal; SCImago; thử Scopus Sources và Clarivate MJL/JCR; ACL Anthology; Google Colab FAQ. Truy vấn chính: “site.ueh.edu.vn hỗ trợ chi phí công bố quốc tế sinh viên”, “491 tài trợ thưởng UEH 2026 thay thế”, tên journal + SJR 2025 + subject category, tên journal + author guidelines/fees. Không có quyền đăng nhập JCR trong phiên; không suy hạng chính thức từ site tổng hợp. SCImago có một số trang 403; ghi riêng từng trường hợp. Đối chiếu chính sách tại thời điểm nộp.

- [J1] https://profile.jucs.org/
- [S1] https://www.scimagojr.com/journalsearch.php?q=145537&tip=sid
- [J2] https://jlm.ipipan.waw.pl/index.php/JLM/about
- [S2] https://www.scimagojr.com/journalsearch.php?clean=0&q=21101039901&tip=sid
- [J3] https://journal.iberamia.org/index.php/intartif/about
- [J3m] https://journal.iberamia.org/index.php/intartif/journalmetrics
- [S3] https://www.scimagojr.com/journalsearch.php?clean=0&q=24258&tip=sid
- [S3-secondary] https://journalsuggester.com/journal/24258
- [J4] https://mitpress.mit.edu/open-access-at-mit-press/journals/
- [J4-author] https://transacl.org/ojs/index.php/tacl/about/submissions
- [S4] https://www.scimagojr.com/journalsearch.php?clean=0&q=21101049047&tip=sid
- [J5] https://www.jmlr.org/author-info.html
- [S5] https://www.scimagojr.com/journalsearch.php?q=20969&tip=sid
- [P1] https://jlm.ipipan.waw.pl/index.php/JLM/article/download/457/301/3897
- [P2] https://aclanthology.org/2023.tacl-1.73/
- [P3] https://jmlr.org/papers/v25/23-0568.html
- J.UCS example 2024: https://doi.org/10.3897/jucs.118889
- J.UCS example 2025: https://doi.org/10.3897/jucs.137103
- IA example: https://journal.iberamia.org/index.php/intartif/article/view/1890
