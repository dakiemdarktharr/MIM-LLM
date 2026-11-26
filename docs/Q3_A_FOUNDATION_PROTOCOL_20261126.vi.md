# Q3-A — một phương án thay nền ngôn ngữ có giới hạn

Chốt ngày 26/11/2026, trước optimizer của phương án này. Đây là sửa feasibility
sau hai pilot byte thất bại, **không** mở thêm lượt calibration2. Giữ nguyên các
kết quả âm, câu hỏi standalone A1−A2 và các bài độc lập. Mục tiêu cuối vẫn là LM
hội thoại MIM; hai baseline ở đây chưa chứa MIM và không chứng minh năng lực chat.

## Lý do và biến đã đổi

Reference TinyStories chỉ cho chẩn đoán, không phải matched comparison. Không
dùng trọng số ngoài có license chưa xác minh. Giữ nguyên tokenizer GPT-Neo
50257 token, revision/JSON hash trong `reference_diagnostic_results.json`; card
tokenizer MIT đã kiểm tra. Không fit, prune hoặc đổi merges/vocab. Đây là thay
nhiều yếu tố tokenizer/capacity/corpus/curriculum; không gọi tokenizer ablation.
PPL chỉ so sánh trực tiếp trong cùng tokenizer và cùng tập mục tiêu.

TinyStories revision `f54c09fd23315a6f9c86f9dc80f725de7d8f9c64`,
CDLA-Sharing-1.0. 300000 train, giữ nguyên 300 validation và 300 test cũ từng
hàng. Phần thêm chỉ upstream train; loại digest toàn truyện sau NFKC/casefold/
gộp whitespace, không tuyên bố loại semantic near duplicate. Corpus hash
`f1af895c66d7d689dfb794619cd6d91f658ce221ab29d0c27b71f9401556ffbc`.
Đã bỏ 37282 candidate trùng normalized với các nguồn đã giữ. Test chỉ dùng để
giữ split/loại va chạm nguồn, chưa token hóa và chưa đo performance.

LM: 300169 cửa sổ train, 66859228 targets/một lượt; mọi target truyện dài được
giữ đúng một lần qua các cửa sổ reset độc lập, context1024. SFT train:271170
rows,10708980 response-targets/lượt; unconditional135905/conditional135265.
SFT là viết ba câu/tiếp hai câu bằng ba câu, tách câu bảo thủ như protocol cũ,
không nhãn trạng thái. Các exclusion dài/context được đếm trong manifest.
Validation LM61573targets/300sources; SFT12192targets/312rows. Chưa nhãn người.

Input/label dịch một token; SFT chỉ tính CE trên response và EOS. BOS/EOS/PAD
đều50256 nhưng mask theo **độ dài**, không theo token ID. Token0 là văn bản hợp
lệ. Newline phân cách prompt/response, assert BPE encode nguyên chuỗi khớp ghép
từng phần; không cho answer token lọt vào prefix. Chỉ chiếu LM head ở vị trí có
nhãn, gradient/CE đã kiểm tra khớp loss dense; không bỏ context khỏi backbone.

## Backbone, lịch và kiểm tra

Transformer GELU/pre-LN8layers/64width/4heads, absolute position1024, tied lexical
head; **3681984** tham số (lexical3216448,position65536,other400000). Đây là
project baseline, không phải GPT-Neo. Các layer clone được khởi tạo độc lập.
Factorized linear-candidate minGRU2layers/width325/embedding64, tied head:
**3682887** tham số (lexical3216448,other466439). Đây là biến thể của dự án,
không phải toàn bộ stack minGRU gốc. Chênh903params~0,0245%; positional budget
và functional capacity vẫn khác nhau. Cùng lexical initialization seed0,
không nhận toàn bộ backbone là cùng initialization.

Hai seed0 mới: mỗi model80M LMtargets rồi20M SFTtargets, AdamWfloat32,
batch4/dropout0, clip1; weightdecay0,1 cho matrix và0 cho bias/norm. LR LM0,001
warmup0,5M targets/cosine xuống0,0001; SFT reset optimizer moments, LR0,0003,
warmup0,1M/cosine xuống0,00003. Thứ tự nguồn shuffle seed0+stage/epoch được
khôi phục với cursor; không gọi khác GPU là bitwise same trajectory. Dừng đúng
budgettarget kể cả batch cuối. Lưu checkpoint stage-LM trước SFT và final; chưa
có quyền dùng các checkpoint này để train B/C/Q1 hay postmatrix.

12 unit checks không optimizer và4 engineering tests thật trên fixture tổng hợp
đã đạt: tiny batch thuộc, exact CPU full-vs-interrupted resume qua chuyển stage,
CE/gradient selectedhead=dense, reset/padding/causality/cache/EOS. Chúng không
là scientific scores; không nói fixture đã chứng minh production overfit.
Lượt GPU đầu còn phải qua path checks production IDs/context rồi đo thông lượng,
VRAM, token/s và finite objectives. Không dùng thông lượng byte cũ làm số đo BPE.

Train-only audit cặp A1/A2: toàn bộ6000khớp BPE inputlength/editdistance/Hamming/
invariant reference tokens và prompt-response boundary;0mismatch. Đây không
là bằng chứng mọi lexical/causal nuisance đã bằng nhau. Không cần regenerate
dataset chỉ vì đổi tokenizer. Audit source snapshot/hash có receipt riêng.

## Giới hạn và quyết định tiếp

Tối đa8lượt driver×1100s **soft** cap, first GPU session mục tiêu20phút gồm
setup/sync; ledger reserve trước cập nhật kể cả crash. Không tự thêm lượt hoặc
mua CU. ChỉT4/L4, đọc UI rate thực<=6CU/giờ, balance>=20; dừng nếu observed
balance drop từ lúc đầu>=16CU, kể cả debit có workload khác không tách được.
Các ngưỡng này là cap, không phải chi phí được đo hay bảo đảm đủ100M/model.
CPU data preparation/test thời gian riêng; không gán thành GPU-hours.

Sau lượt đầu đọc lại archive qua Drive connector, kiểm hashes/metric sums,
finite gradients/VRAM, throughput và estimate thời gian còn lại theo chính máy.
Nếu estimate không đủ trong cap, không thu nhỏ âm thầm target để gọi complete:
báo incomplete và xem lại feasibility. Không đổi cấu hình/seed để săn A1 thắng.
Nếu quáfit/loss khôngfinite/lặp viết không bám prefix: giữ failure, dừng/thu hẹp
hoặc gộp nghiên cứu theo evidence; không tự chạy calibration kế tiếp.

Khi hai nền hoàn tất, giữ toàn bộ16prefix đã dùng và một unconditional prompt
mỗi model, format newline đã học; raw prefix diagnostic báo riêng, không chọn
decode seed đẹp. T0,8/topk40/seed17/max128BPE, human label null đến lúc người thật
đọc. Đánh giá đủ mẫu về3–5câu tự nhiên/bám prefix/tạo sự kiện, báo lặp/cap/né viết;
assistant chỉ sàng lọc feasibility, không thay nhãn người. User hiện là người
đọc duy nhất; chưa có agreement hai người hay blind human evidence.

Chỉ sau writing gate có căn cứ mới mở contrasts/seeds với plan mới. Không mở
test, train B/C/Q1, fit tokenizer hoặc compile LaTeX trong phương án này. Goal
toàn Q3-A vẫn active; chưa có submission/acceptance/publication mới.

## Resource amendment trước cập nhật đầu tiên

Lượt upload/bootstrap L4 riêng đã lưu bundle92.702.119bytes/SHA
`b1c97087a3415fc4c1b65dc4fa5a8496917ded649087add55d40352bec55e5d9`,
73members+manifest,0optimizer,0driver reservations rồi trảGPU. UI597,61→597,34
CU là hai quan sát balance, chưa phải hóa đơn quy thuộc. Không dùng thời gian
tải92MBtừmáylocal làm throughputtrain. Lượt train đầu chọn `--wall-seconds 900`
(ngắn hơn1100maximum) để dành chỗ mount/preflight/sync trong20phútsoftcap;
vẫn tính1/8invocations, không bù200giây bằng lượt bổ sung. Các lượt sau tối đa1100.
Driver ghi reserved cap thực trong ledger và bác số vượt1100. Sửa orchestration
này không đổi scientific source fingerprints/plan/model/data/exposure. Giữ v1ZIP
trênDrive; overlay script mới có SHA riêng, phải kiểm trước copy vào scratch,
lưu versioned source trênDrive và chỉ sau đó mới chạy. Không âm thầm sửa bundle.

## Sau lượt đo đầu — sửa quản lý phiên và đo phần còn thiếu

Do hai mount timeout, lượt đầu thực tế chọn360s, vẫn chiếm1/8slot (không bù slot).
Đủ6.559.500LMtargets/7366updates Transformer,296,568s cập nhật và342,991s driver;
chưa minGRU/SFT. Archive và metric accounting được đọc độc lập sau UI0sessions.
Chi tiết tại [báo cáo lượt1](Q3_A_FOUNDATION_INVOCATION1_20261126.vi.md).

Child `runtime.unassign()` ném lỗi khi gọi callback JavaScript ngoài IPython,
sau khi export đã lưu. UI xác nhận0sessions; không quy chính xác tác nhân trảVM
từ riêng traceback. V3 bỏ lời gọi này khỏi child; **notebook host** chịu trách
nhiệm flush/unmount Drive rồi unassign trong finally, kể cả subprocess lỗi.
Giữ source/bundle v1,v2 cùng log lỗi; V3 overlay phải có digest riêng.

Trước optimizer kế tiếp, một probe không optimizer sẽ lấy32batch đầu theo thứ
tự train seed0/epoch0 của từng stage cho mỗi backbone;2batch backward khởi động
cũng không cập nhật. Kiểm mọi learned parameter bất biến, gradients finite,
ghi batch/target/input counts/VRAM và forward+backward seconds. Đây chỉ là
compute-only throughput ở random initialization: thiếu AdamW/host/log/validation/
Drive và không phải chất lượng LM. Không profile validation/test hoặc sinh văn
bản để chọn thay đổi. Probe thêm không tạo scientific training exposure.

Sau probe, tính lower-bound thời gian còn lại theo stage/target chưa học, đối
chiếu7700s maximum của7driver còn lại và balance thực. Nếu ngay lower bound đã
vượt cap thì không mở driver2 dưới lời hứa rằng đủ ngân sách; phải báo resource
infeasibility và quyết định tiếp theo trước mọi cập nhật. Nếu lower bound nằm
dưới cap cũng chưa bảo đảm đủ, vẫn giữ giới hạn8slot/16CU observed drop và báo
incomplete khi cần. Không dùng chẩn đoán này để mở test hoặc săn hiệu ứng A1−A2.

## Resource-only annex sau profile, trước driver2

Profile L4 cho optimistic8042s >7700s còn lại. Trần8lượt là giả định kỹ thuật
của agent; quyền người dùng hiện có yêu cầu hoàn thànhQ3-A bằng CU đang có.
Annex `configs/q3a/foundation_resource_annex.json` có hash riêng và hiệu lực
trước driver2 thay trần8 bằng16lượt, giữ1100s/lượt và trần16CU từUI597,61.
Không đổi learning plan c18/model/data/seed/targets/tokenizer/decoding. Ledger
lưu annex riêng, verifier kiểm annex và source profile; không sửa receipt cũ.
Chi tiết `docs/Q3_A_FOUNDATION_RESOURCE_PROFILE_20261126.vi.md`.

Theo yêu cầu mới của người dùng, giữ Drive mount/VM giữa những bước hợp lệ tiếp
ngay trong cùng phiên; không unassign chỉ vì xong một driver. Host chỉ flush/
unmount/unassign ở cuối công việc hoặc khi lỗi/cap làm không thể tiếp tục.
Chính sách tại `docs/COLAB_DRIVE_SESSION_POLICY_20261126.vi.md`. Những dòng
8slot và host-finally sau mỗi driver ở phần cũ là lịch sử trước annex này.
