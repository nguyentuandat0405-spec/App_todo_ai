# Todo App Assignment Manager 📚

Đây là một ứng dụng quản lý bận rộn và bài tập (Deadline/Assignment) thông minh, hỗ trợ bởi Google Gemini AI. Ứng dụng giúp bạn tối ưu hóa thời gian học tập, sắp xếp thứ tự ưu tiên công việc dựa trên lịch học và nhắc nhở thời gian rảnh.

## 🌟 Các tính năng chính
- **Quản lý bài tập (Deadline)**: Thêm, sửa, xóa, đánh dấu hoàn thành bài tập với tính toán thời gian thực tế đếm ngược.
- **Thời khóa biểu & Lịch bận**: Nhập lịch học và các lịch trình cá nhân để AI tự động đánh giá và gợi ý thời gian học hợp lý nhất.
- **Trí tuệ nhân tạo (AI)**:
  - Tự động nhận diện môn học, hạn nộp từ hình ảnh bài tập (OCR bằng Gemini).
  - Gợi ý thứ tự ưu tiên làm bài tập dựa trên deadline và lịch trống của bạn.
- **Pomodoro Timer**: Bộ đếm thời gian tập trung 25 phút tích hợp ngay trên từng bài tập.
- **Biểu đồ thống kê**: Trực quan hóa tiến độ hoàn thành bài tập và số lượng công việc theo từng môn học.

## 🚀 Hướng dẫn cài đặt từng bước

### 1. Tải về và cài đặt thư viện
Yêu cầu máy tính của bạn đã cài đặt Python. Mở Command Prompt (Terminal) tại thư mục chứa dự án và chạy lệnh sau để cài các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

### 2. Tạo file cấu hình bảo mật `config.json`
Để bảo mật các API Key của bạn (không bị lộ lên mạng), dự án sử dụng file cấu hình.
1. Trong thư mục dự án, bạn sẽ thấy file mẫu tên là `config.example.json`.
2. Hãy **copy** file đó và đổi tên bản sao thành `config.json`.
3. Mở file `config.json` và điền các API Key của bạn vào:

```json
{
    "gemini_api_key": "ĐIỀN_GEMINI_API_KEY_CỦA_BẠN_VÀO_ĐÂY",
    "backup_api_key": "ĐIỀN_GROQ_HOẶC_OPENAI_KEY_DỰ_PHÒNG_(Tùy_chọn)",
    "telegram_token": "ĐIỀN_TELEGRAM_BOT_TOKEN_CỦA_BẠN",
    "telegram_chat_id": "ĐIỀN_TELEGRAM_CHAT_ID_CỦA_BẠN",
    "telegram_schedule_time": "06:30"
}
```

*Lưu ý: File `config.json` đã được đưa vào `.gitignore` nên bạn hoàn toàn yên tâm khi đẩy code lên GitHub.*

### 3. Khởi chạy ứng dụng
Chạy ứng dụng cực kỳ đơn giản bằng 1 trong 2 cách:

- **Cách 1**: Chạy trực tiếp script bằng cách nhấp đúp vào file `Mo_todo_App.vbs`. Cửa sổ console sẽ hiện ra và ứng dụng tự động bật trên trình duyệt của bạn. Bạn có thể tắt cửa sổ console để dừng ứng dụng hoàn toàn.
- **Cách 2**: Chạy qua Terminal/Command Prompt bằng lệnh:
  ```bash
  streamlit run app.py
  ```

🎉 **Chúc bạn có những giờ phút học tập hiệu quả, không trễ deadline!**
