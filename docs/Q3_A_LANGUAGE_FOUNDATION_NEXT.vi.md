# Q3-A — công việc kế tiếp sau writing gate thất bại

> Cập nhật 27/11: phương án subword c18 đã hoàn tất cả hai parent seed 0
> (80M LM + 20M SFT mỗi model), được audit độc lập và đã sinh 34 mẫu thật.
> CSV tác giả vẫn trống; xem [audit cuối](Q3_A_FOUNDATION_INVOCATION13_20261127.vi.md).
> Các bước chuẩn bị ngày 26/11 dưới đây là lịch sử, không phải lệnh chạy lại.
> Bước hiện hành là nhãn người thật và review evidence trước khi mở rộng;
> không fit tokenizer, đổi ngưỡng hoặc train lại để tìm kết quả thuận chiều.

26/11/2026. Đây là hàng đợi chuẩn bị, **chưa phải run plan hay lệnh train**.
Calibration2 đủ 3/3 lượt; không thêm lượt thứ tư hoặc chạy A0–A3 theo plan cũ.

Nguồn quyết định: [kết quả calibration](Q3_A_CALIBRATION2_RESULTS_20261126.vi.md)
và [reference/tokenizer profile](Q3_A_REFERENCE_DIAGNOSTIC_20261126.vi.md).
Byte/BPE ratio 4,02 và suffix 63 byte/15 subword cho thấy một thay đổi đơn vị
token cũng đổi số bước hồi quy; chúng chưa chứng minh nguyên nhân thiếu chất lượng.

1. Chuẩn bị **một phương án thay thế có giới hạn** cho nền ngôn ngữ, ưu tiên
   tokenizer GPT-Neo đã phát hành và giữ nguyên vocab/merges (không fitting).
   Đếm tham số thực sau instantiate cả recurrent và Transformer; không sao chép
   tên “1M” hoặc dùng trọng số ngoài chưa rõ license làm parent.
2. Đối chiếu số văn bản/byte đã xem, số subword targets và độ dài context.
   Tăng training tokens sau đổi tokenizer cũng tăng exposure theo văn bản;
   không gọi đó là ablation chỉ đổi tokenizer. Chốt train-source expansion,
   nguyên held-out groups, filtering/windowing và hashes trước optimizer.
   Không âm thầm bỏ 1.015 truyện train dài hơn 512 subword inputs.
3. Kiểm tra cả lexical capacity/embedding và lịch general LM → instruction
   adaptation. Nếu thay nhiều yếu tố, gọi là sửa nền feasibility; không gán
   cải thiện cho MIM hoặc một yếu tố đơn lẻ. Giữ các kết quả âm đã có.
4. Nếu dùng subword, kiểm tra mask/shift tại ranh giới prompt-response, EOS/pad,
   reset và step/cache. Kiểm tra lại **tokenized input length và edit counts**
   của A1/A2 trên train; byte-matched không tự thành BPE-token-matched. Mọi sửa
   benchmark cần dataset/plan version mới trước post-training, giữ bản cũ.
5. Hoàn thiện mã, preflight không optimizer, overfit/resume checks được cấp
   cho đúng Q3-A run IDs, rồi khai báo plan/caps mới. Ưu tiên một cặp mạnh;
   GPU probe đầu vẫn có soft cap 20 phút, đo VRAM/thông lượng/CU thật trước
   quyết định chạy tiếp. Chốt giới hạn tổng và stop conditions trước job;
   không dùng thông lượng byte LM làm phép đo cho softmax 50.257 lớp.
6. Chỉ mở primary contrasts khi có căn cứ về viết/bám prefix. Sau đó mới chốt
   transfer/rubric/mẫu blind và đủ bằng chứng thống kê; người thứ hai còn thiếu.
   Không thay human labels bằng assistant/parser để vượt gate.

Giữ câu hỏi standalone A1−A2, training/selection caps cân đối cho ba nghiên cứu
và mục tiêu dài hạn mô hình hội thoại MIM. Nếu một nền ngôn ngữ được dùng chung,
theo dõi chi phí/nguồn/parent thật một lần và công khai reuse; không gọi warm-up
chung là đóng góp khoa học độc lập của ba bài. B/C/Q1 training, tokenizer fit,
mua CU và compile LaTeX vẫn chưa được mở bởi tài liệu này. Goal vẫn active.
