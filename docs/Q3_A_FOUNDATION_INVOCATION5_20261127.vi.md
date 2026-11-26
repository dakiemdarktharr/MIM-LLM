# Foundation lượt5: xong LM, SFT một phần — 27/11/2026

Session`20261126T174855Z`, TeslaT4/FP32/PyTorch2.14.1+cu130; cùng mount Drive,
reviewed MHA inference fastpathFalse. Transformer baseline **3.681.984tham số**,
chưa chứa MIM; minGRU **3.682.887tham số** chưa bắt đầu. Foundation chưa xong.

| Đại lượng đã xác minh độc lập | Giá trị |
|---|---:|
| LM targets | 80.000.000/80.000.000 |
| SFT response targets | 2.785.836/20.000.000 |
| Cumulative targets / input tokens | 82.785.836 /84.628.422 |
| Cumulative updates | 107.402 |
| New targets / updates lượt5 | 11.890.681 /27.848 |
| Optimizer train seconds lượt5 | 982,907441266 |
| Driver seconds / soft reserved | 1.084,540022785 /1.100 |
| LM targets/optimizer-train second lượt5 | 21.255,330127 |
| SFT targets/optimizer-train second lượt5 | 5.023,583095 |

SFT chỉ tính CE trên continuation, gồm EOS; prompt vẫn được xử lý và tính riêng
input exposure. 2.785.836SFT labels dùng4.628.422input tokens, không giả hai
đại lượng bằng nhau hoặc lấy thông lượng LM dự báo toàn SFT. Thông lượng trên
loại host/Drive/setup, không là thông lượng hoặc hóa đơn toàn phiên.

Kết thúc80M LM: validation61573BPE targets cho CE2,241714497/PPL9,409449942,
chưa phải PPL **sau SFT** hoặc metric viết/logic. Không so PPL trực tiếp với byte
tokenizer lịch sử. SFT language quality và conditioning còn chờ fixed review;
không suy từ một train-window diagnostic loss thành chất lượng held-out.

Archive120.757.057bytes/SHA
`25b95a92accc88d23f8d23e84afdd7ad73cd156888caa49d889927d6e5421709`
được tải lại từ Drive:57members/107.402metricrows liên tục và finite,
per-stage/counter/annex/checkpoint hashes kiểm; không pickle/optimizer. Readback
khi VM còn mount. Latest
`d6d4c25434578b832da5a5d239dff27d36252217fb1b41f4b1c47029a61dbde4`;
LM-final
`84ce54dc104013da04e98100b2654fa5bb122a24dcac275116b2a6751644b81c`;
previous
`5d27bbca642cc19e8ce9fff86a80c4a8fa1dc3f580cab0f985a818df496d9079`.

Checkpoint mới được kiểm với **cùng contract trước lượt5**, không nới ngưỡng:
FP64 max path error1,08358e-13,0argmax mismatch, max decode-policyL1=
1,3306733118687974e-5<1e-4; loss/grad flag check bitwise bằng nhau, weights
không đổi,0optimizer. Cloud report SHA
`c061356084469a0c2cdbaad66245afa5a06a6c89a90054e8409dd58c3120b31e`
đã tải lại và qua gate local. Kết quả này không viết lại các fail FP32 ở weights
cũ hoặc là bằng chứng hiệu ứng khoa học. Vẫn cần kiểm ở checkpoint tiếp theo.

5/16slots dùng; UI592,27CU/rate khoảng1,87CUh, không invoice quy thuộc hoặc mua
CU mới. Lượt6 session`20261126T181247Z` đã được reserve1100s sau audit/proof;
không coi reservation là xong lượt6. Giữ mount, learningplan c18/targets/seeds/
optimizer và permissions không đổi. JSON: `configs/q3a/foundation_invocation5_results.json`.

Chưa có writing outputs theo fixed review hai complete parents, human labels,
A0–A3post/test/LaTeX hoặc milestone submission/acceptance/publication.
