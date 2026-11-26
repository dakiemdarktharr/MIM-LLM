# Q3-A: kiểm tra lớp phân tích — 26/11/2026

Đây là sửa lỗi phương pháp trước khi có kết quả khoa học. Chưa có nhãn người
thật, checkpoint khoa học trên Drive hoặc kết quả test được xác minh. Các nhãn
trong unit test đều là dữ liệu hư cấu, chỉ nằm trong thư mục tạm khi chạy test.

## Hai điểm đã sửa

1. Bộ phân tích cũ lấy coverage/fluency của reader A khi không có adjudication.
   Lớp mới lấy trung bình hai reader cho từng output, rồi tổng hợp theo
   backbone/arm/training seed. Nếu có CSV phân xử đầy đủ, dùng điểm đã phân xử.
   Bất đồng ở nhãn logic/format vẫn yêu cầu phân xử trước khi có primary result.
2. Chỉ ghép A1/A2 trong từng seed chưa đủ: một source có thể mất ở cả hai arm
   trong cùng seed. Lớp mới yêu cầu tích đầy đủ của source × role × training seed
   × decoding seed × backbone × các arm được khai báo. Không tự bỏ output lỗi.

Lớp mới là `src/mim_llm/q3a_reviewed_analysis.py`, phiên bản
`q3a-reviewed-quality-1`. Nó dùng lại phán định primary và bootstrap đã khóa,
không sửa `q3a/evaluate.py`, trọng số hoặc dữ liệu train. Không thay bundle đang
chờ chạy trên Colab bằng bundle khác một cách ngầm định.

## Primary và độ bất định

Gọi s(r) là 1 khi continuation r đúng mọi mệnh đề bắt buộc, có 3–5 câu, không
mâu thuẫn và không unclear; ngược lại là 0. Với mỗi source và mỗi lần chạy:

`Y = [s(base)s(effective) + s(base)s(noop)] / 2`.

Hiệu A1−A2 được lấy theo cùng source, rồi lấy trung bình các seed đã quan sát
trong source trước khi bootstrap source. Cặp truyện, role, hệ thống và seed của
một source đi cùng một cụm; không coi các câu là mẫu độc lập. Báo riêng hiệu ứng
từng training seed/decoding seed. Khoảng tin cậy theo source có điều kiện trên
các training seed đã quan sát; không phải bảo đảm độ ổn định trên seed mới.

`clean_utf8_fraction` là thước đo viết thứ cấp: tỷ lệ output không có ký tự
thay thế U+FFFD, theo quy tắc của generator đã khóa. Tên trường `valid_utf8` cũ
cũng dùng quy tắc này; không nên diễn giải nó là kiểm chứng ngữ pháp hoặc độ
trôi chảy. Byte lỗi hoặc output quá chung vẫn giữ trong mẫu chấm. Không âm thầm
thêm điều kiện máy vào primary sau khi xem kết quả; format/logic primary vẫn
do người đọc chấm theo rubric. Những hạn chế này phải được ghi trong Methods.

## Hợp đồng dữ liệu và khóa test

CLI kiểm tra plan bằng loader gốc, run đúng khai báo và generation ID; đối
chiếu prompt, scenario ID, world, mệnh đề bắt buộc, facts và pair definitions
với source đã khóa. Private key và các file generation phải khớp một-một,
không có bản ghi thừa/thiếu/lặp. Continuation phải giải mã đúng từ token IDs gốc.
Kết quả lưu SHA của code phân tích, bộ phân tích primary, generation files,
private key, hai CSV nhãn, CSV phân xử nếu có và selection.

Trước final test, điền bản sao của
`configs/q3a/preregistration.template.json`: effect tối thiểu hữu ích, cap
GPU-giờ hữu hạn sau calibration, nguồn/cách lấy mẫu, `test_arms`, và SHA của
module phân tích. Template còn `null` là draft, không phải đăng ký hoàn tất.
Không chọn source/arm sau khi xem output. Nếu chỉ đủ công sức chấm A1/A2,
khai báo hai arm này trước test và nêu rõ secondary arms chưa được chấm;
training matrix và yêu cầu freeze đủ 24 checkpoint vẫn giữ nguyên.

Lấy SHA chuẩn hóa newline dùng chung Windows/Colab:

```powershell
python -c "from mim_llm.q3a.io import source_sha256; import mim_llm.q3a_reviewed_analysis as a; print(source_sha256(a.__file__))"
```

Sau `freeze-selection` và thu thập nhãn người thật, phân tích bằng:

```powershell
python -m mim_llm.q3a_reviewed_analysis --plan PLAN --selection SELECTION --labels-a READER_A_CSV --labels-b READER_B_CSV --key PRIVATE_KEY --generations GENERATION_1 GENERATION_2 --output NEW_RESULT_JSON
```

Thêm `--adjudicated ADJUDICATED_CSV` khi cần. Với validation, bỏ `--selection`.
CSV phân xử phải đầy đủ và có evidence; không tự sinh nhãn để lệnh chạy được.
Đường dẫn output phải mới. Công cụ này là phân tích nội bộ, không tự tạo dấu
thời gian đăng ký công khai; nếu đổi code/quy tắc sau test, giữ bản cũ và công
khai amendment/phân tích khám phá, không gắn lại nhãn preregistered.

## Bằng chứng kỹ thuật

15 test mới kiểm tra hai reader, phân xử, bất đồng chưa giải quyết, thiếu cả
source/seed/backbone/arm, generation bị sửa, byte lỗi, khóa test và đường CLI.
CLI unit fixture thay loader bằng plan hư cấu; kiểm tra loader/data/fingerprint
thật nằm trong suite gốc và kiểm tra plan hiện hành riêng. Không đánh đồng
unit fixture với thử nghiệm mô hình hoặc đánh giá người thật.

Plan hiện hành vẫn là
`ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142`;
bundle vẫn SHA256
`2ad7e8d63189ffc84b5802cf31df01950d596bc2d57021a56f8f9e7240ac6f2b`.

Các gate còn mở: quyền Drive, writing feasibility, throughput/CU thực, training
matrix, pilot người đọc/cỡ mẫu/transfer có giấy phép, đăng ký phân tích cuối và
bản thảo có kết quả thật. Test phần mềm không chứng minh bài đủ giá trị Q3.
