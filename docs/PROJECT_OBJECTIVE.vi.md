# Mục tiêu dài hạn của MIM-LLM

Người dùng xác nhận ngày **26/11/2026**: xây một mô hình ngôn ngữ tự hồi quy
dựa trên cơ chế MIM, có khả năng **hội thoại nhiều lượt hoàn chỉnh**, với trải
nghiệm trò chuyện kiểu các thế hệ ChatGPT ban đầu làm mốc kỳ vọng định tính.
Đây là mục tiêu phát triển, chưa phải khả năng đã đo hoặc cam kết tương đương.

Mục tiêu không dừng ở sinh đoạn truyện, trả lời nhãn trạng thái hay hoàn thành
bốn bản thảo. Ba nghiên cứu Q3 vẫn độc lập, chia đều trần huấn luyện như kế
hoạch hiện hành. Q1 cần đóng góp khoa học riêng; việc xuất bản không thay bằng
chứng về khả năng trò chuyện. Quan hệ tái sử dụng giữa các bài được ghi nội bộ,
không thêm lời tuyên bố một bài phục vụ bài khác vào manuscript.

## Khả năng cần xây và đo

- Hiểu yêu cầu và tạo câu trả lời tự nhiên, có ích, phù hợp lượt hỏi.
- Hội thoại nhiều lượt: giải quyết câu hỏi nối tiếp, tham chiếu người/vật và
  dữ kiện đã nói, cập nhật khi người dùng sửa thông tin, xử lý đổi chủ đề.
- Duy trì nhất quán với cả lịch sử người dùng và sự kiện do mô hình tự sinh;
  phân biệt tình huống thật với giả định. Đo riêng lợi ích bộ nhớ nội tại.
- Trả lời, giải thích và trao đổi trên nhiều loại nhiệm vụ; biết hỏi làm rõ
  khi cần và thể hiện sự không chắc chắn. Đánh giá tính đúng của thông tin
  riêng, không đồng nhất nói trôi chảy hoặc không tự mâu thuẫn với nói đúng.

Ngôn ngữ, miền nhiệm vụ, độ dài hội thoại và tiêu chí đạt phải được chốt trước
đánh giá tương ứng. Không dùng cụm “như ChatGPT đời đầu” thay cho bộ tiêu chí.

## Lộ trình kỹ thuật có điều kiện

1. **Nền ngôn ngữ:** pretrain bằng dự đoán token tiếp theo trên corpus đủ rộng,
   có kiểm tra giấy phép và tách nguồn. Đo năng lực sinh văn bản chung bên cạnh
   benchmark logic. Prototype MIM-LM nhỏ dùng để kiểm tra cơ chế và tính khả thi.
2. **Học hội thoại:** supervised fine-tuning (SFT) trên instruction và hội thoại
   nhiều lượt có nguồn gốc/giấy phép phù hợp. SFT là huấn luyện bằng ví dụ yêu
   cầu–câu trả lời; định dạng vai trò và vị trí tính loss phải được đặc tả.
   Không giả định base LM tự trở thành assistant chỉ nhờ thêm giao diện chat.
3. **Đánh giá tách biệt:** usefulness/instruction following, liên kết giữa các
   lượt, sử dụng dữ kiện/sửa đổi, logic, factual reliability và chất lượng văn
   bản. So với Transformer và recurrent controls được tiếp cận cùng dữ liệu,
   thông tin và ngân sách; kiểm tra mù của người đọc dùng nhãn thật.
4. **Mở rộng sau bằng chứng:** tăng dữ liệu, kích thước hoặc post-training khi
   pilot chứng minh khả năng học ngôn ngữ/hội thoại và thông lượng đo được cho
   phép. Đo VRAM, tốc độ train/inference, tổng compute và chất lượng theo quy mô.
   Không suy ra quy mô cần thiết hoặc thời gian/chi phí từ tham vọng sản phẩm.

Không khóa ứng viên branch-residual thành kiến trúc cuối trước kiểm tra tính mới
và hiệu quả. Cơ chế MIM-N → MIM-S và sai phân tường minh tiếp tục là giả thuyết
cần đối chiếu với learned-pair; kết quả âm có thể đòi sửa kiến trúc.

## Các mốc phải theo dõi riêng

| Mốc khả năng | Bằng chứng cần có | Trạng thái ngày xác nhận |
|---|---|---|
| Học ngôn ngữ và viết tiếp ở prototype | Sinh tự do, perplexity giữ riêng, chất lượng/logic và tài nguyên đo thực | Chưa có bằng chứng đủ cho general chat |
| Assistant hội thoại cơ bản | Pipeline SFT thật và đánh giá instruction/multi-turn trên nguồn chưa dùng chọn cấu hình | Chưa xác lập |
| Hội thoại nhiều lượt hữu ích | Bộ nhiệm vụ đa dạng, nhãn người độc lập, kết quả theo độ dài/lỗi và đối chứng mạnh | Chưa xác lập |
| Mức trải nghiệm mong muốn | Tiêu chí định lượng/định tính công khai, đánh giá có kiểm soát | Mục tiêu tham vọng, chưa chứng minh |

Các mốc manuscript drafted, submitted, accepted, published vẫn theo dõi riêng
trong [status](STATUS.md). Không có train, dữ liệu, nhãn hoặc kết quả mới phát
sinh từ việc ghi nhận mục tiêu này. [Kế hoạch bốn bài](PORTFOLIO_V3.vi.md) vẫn
có điều kiện và không thay thế lộ trình xây mô hình hội thoại.
