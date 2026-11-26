# Foundation lượt2: resume thật và cloud audit — 26/11/2026

Session`20261126T144537Z`, c18learning plan và resource-only annex
`1b22c463e3d8…`, L4/PyTorch2.14.1+cu130/FP32. Transformer baseline thực
**3.681.984 tham số**, chưa chứa MIM. Lượt2 hoàn tất driver cap, **chưa** hoàn
tất foundation100Mtargets/model hoặc nghiên cứuQ3-A.

| Đại lượng đã đo | Giá trị |
|---|---:|
| Tổng LM targets Transformer | 28.053.669 / 80.000.000 |
| SFT targets Transformer | 0 / 20.000.000 |
| minGRU LM/SFT targets | 0 / 0 |
| Tổng updates | 31.489 |
| Targets / updates thêm trong lượt2 | 21.494.169 / 24.123 |
| Optimizer training seconds thêm | 978,122649556 |
| Targets / optimizer-train second | 21.974,9220711 |
| Driver seconds / reserved soft cap | 1.083,28627213 / 1.100 |
| Peak allocated bytes lớn nhất lượt2 | 2.091.562.496 |
| Train CE,100updates mới đầu /100updates cuối | 2,887675 / 2,581101 |

CE lấy trung bình có trọng số target trên **các batch train khác nhau**; không
phải validation PPL, điểm viết hoặc hiệu ứngA1−A2. Throughput optimizer đã gồm
forward/backward/clip/AdamW, nhưng loại host/log/Drive/setup và validation.
Không dùng profile forward/backward ngắn thay số đo toàn driver.

Checkpointlatest SHA
`c0d66aa6f84f725cc3690e59714f7a05aa8c6bbbcb4e27f9c35d2ebde8c67985`;
previous
`1b8b8afe85ee02f1516dfb6e45cdbd1943741ade6eff26668a6090e6e6e79938`.
Chunk đầu nối previous9534ba29f99e… từ lượt1, các previous/latest tiếp nối đúng
thứ tự. Driver returncode0, ledgerfinished, không mở post/test hoặc dùng nhãn.

Archive83.017.079bytes/SHA
`e5a85041ed6b084d06bbdaccfbdb5cf990712dbb507f5df1bf4b865eb62583f7`
đã tải lại bằng Drive connector và kiểm32members,31.489metricrows liên tục,
finite loss/gradient/time/rate, target/input/stage sums và checkpoint/event
hashes. Verifier không loadpickle. Resource annex, evidence hashes và ledger
cũng được kiểm. Đây là cloud readback **khi VM vẫn mount**, không giả là đã
đối chiếu sau release như lượt1. Source/trọng số/lograw/ZIP giữ private/local.

UI595,58CU/rate2,33 là quan sát sau driver; không là hóa đơn quy thuộc. Giữ
mount/VM để tiếp tục trong cap, không mua CU và không yêu cầu quyền Drive lại
cho từng lượt. Đã tiêu thụ2/16driver slots; giữ trần16CU observeddrop từ597,61.
Các lượt sau vẫn phải đọc UI thực và kiểm driver cũ đã terminal/không chạy trùng.

Không có output viết mới, nhãn người thật, primary post matrix, final test,
manuscript có kết quả, submission/acceptance/publication hoặc compileLaTeX.
MinGRU chưa bắt đầu, không suy kết quả hai backbone từ Transformer một phần.
Tóm tắt máy đọc: `configs/q3a/foundation_invocation2_results.json`.
