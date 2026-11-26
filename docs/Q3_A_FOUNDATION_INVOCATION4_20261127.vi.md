# Foundation lượt 4 và cổng số học — 27/11/2026

Session `20261126T171154Z` kết thúc returncode0 trên **TeslaT4 High-RAM**,
PyTorch2.14.1+cu130. Sau khi L4 không cấp được VM, Drive được mount lại, kiểm
đọc/ghi và resume đúng checkpoint466eaf…; giữ nguyên c18learning plan.

| Đại lượng thực | Giá trị |
|---|---:|
| Transformer baseline,tham số thực | 3.681.984 |
| LM targets,tổng / đích | 70.895.155 /80.000.000 |
| SFT targets / đích | 0 /20.000.000 |
| minGRU targets | 0 |
| Tổng updates | 79.554 |
| Targets / updates thêm lượt4 | 20.837.790 /23.380 |
| Optimizer train seconds thêm | 979,044227320 |
| Targets/optimizer-train second | 21.283,808656 |
| Driver elapsed / soft reserved seconds | 1.083,923651715 /1.100 |
| Peak allocated bytes lớn nhất lượt4 | 2.227.155.968 |
| Train CE100updates mới đầu/cuối | 2,430288 /2,238088 |

CE có trọng số targets trên các batch **train khác nhau**, không là held-out
perplexity hoặc khả năng viết. Foundation hai model và nghiên cứuA chưa xong.
Chuyển GPU giữa các invocation phải công khai; đây không là so sánh khớp compute
giữa hai backbone hoặc bằng chứng một backbone tốt hơn.

Archive82.744.948bytes/SHA
`80340b9f834d19a5748b9197549f13dd74e7142cb2bb518e8549c0404b1ca63e`
đã được tải lại qua Drive connector:38members/79.554metricrows liên tục và
finite, per-stage/counter/ledger/annex/event/checkpoint hashes kiểm độc lập,
không loadpickle hoặc optimizer. Readback khi VM còn mount, không phải sau
release. Latest SHA
`3d0328df19087a6432823c69d65d0a49459b7175e7341088f70ddbcb9c5c6210`;
previous
`b7a2dd027b4e59723cf319adda6a12009f9e8f8d918957ec976e4111bb8ad27d`.

4/16driver slots dùng; UI593,52CU/rate khoảng1,87CUh ở quan sát sau train.
Chênh số dư không phải hóa đơn quy thuộc. Không mua CU. JSON kết quả ở
`configs/q3a/foundation_invocation4_results.json`.

## Chưa mở lượt 5: kiểm tra trọng số đã học

Kiểm sau driver dùng copied checkpoint ổn định, không update. MHA fastpath
mặc định của PyTorch cho sai khác train-features/dense-eval tới0,036187917 ở
case512; causality và reset vẫn exact0. Cả5cases **fail** ngưỡng1e-4/1e-4.
Report đã đọc lại độc lập, SHA
`8c9488f11fc144db246f991ea979863b0fd46de90f52f0a2dedc1343bbe29c48`.

Một đối chiếu cùng weights/inputs/threshold, chỉ gọi
`torch.backends.mha.set_fastpath_enabled(False)` trong process kiểm tra:
train-features/dense-eval khớp exact0 ở5cases, dense/full-cache sai khác lớn
nhất3,43323e-5. Tuy nhiên token-step còn sai khác lớn nhất0,000299454 và3cases
dài vẫn **fail** ngưỡng hiện tại. Không đổi threshold hoặc gọi tất cả pass.
Report SHA
`a3250cc38e98c70f3bdab424e5ebd5f9c8d8fa8f47a01b62035a3ea082c7af3d`;
wrapper SHA
`1c13dabe5474810d2b55253b62c9cb1ab96019efe97e4091c8e9d5cf670d2edf`.

API bật/tắt được đối chiếu trong [PyTorch2.10 backend documentation](https://docs.pytorch.org/docs/2.10/backends.html#torch.backends.mha.set_fastpath_enabled).
Hiện mới cô lập một setting gây khác kết quả; chưa tuyên bố đã tìm lỗi upstream
hoặc nguyên nhân kernel cụ thể. Nguồn foundation/model chưa bị sửa. Không lấy
điều này giải thích lại thất bại viết của byte calibration trước đây.

Đang chẩn đoán cùng weights bằng FP64 CPU, đo phân phối token đầy đủ và policy
temperature0,8/top-k40, kiểm loss/grad train khi đổi flag (không optimizer).
Script mới không tự ghi quyền chạy tiếp hoặc ghi đè receipt thất bại. Chỉ sau
khi review bằng chứng mới quyết định backend contract cho lượt tiếp theo.
Giữ mount cho công việc kiểm tra đang chạy, không keepalive giả/giữ GPU vô hạn.

Không có primarypost, test performance, nhãn người, manuscript có kết quả,
submission/acceptance/publication hoặc LaTeX compile. Validation-LM được dùng
cho engineering path checks, không chấm năng lực viết hay hiệu ứng khoa học.
