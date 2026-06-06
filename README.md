
## Hướng dẫn nhanh KLTN — Chạy demo web (Tiếng Việt)

Tệp này hướng dẫn cách chạy demo web (frontend + backend tối thiểu) trên máy local.

## Giới thiệu 
- Dự án này được hoàn thành bởi Lê Thị Ngọc Trâm và Lê Nguyễn Việt Quang, sinh viên chuyên ngành KHMT, ngành CNTT, trường Đại học Khoa học Huế 

## Yêu cầu trước
- Node.js (phiên bản LTS, ví dụ 18+)
- npm (cài cùng Node) hoặc pnpm/yarn
- Python 3.11+ (khuyến nghị dùng virtual environment)
- Tùy chọn: GPU + CUDA nếu bạn muốn chạy mô hình PyTorch nặng trên GPU

## Các bước nhanh (thứ tự khuyến nghị)

1) Backend (tối thiểu)

Ví dụ PowerShell trên Windows:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
# Chạy backend (tùy code, có thể là python main.py hoặc uvicorn)
python main.py
```

Hoặc dùng `uvicorn` nếu project có FastAPI và `main:app`:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Biến môi trường cần đặt trước khi chạy backend (nếu dùng):
- `HUGGINGFACE_TOKEN` (nếu dùng API Hugging Face)
- `GOOGLE_GENAI_API_KEY` (nếu dùng Google GenAI)

Ghi chú:
- Nếu mã yêu cầu checkpoint mô hình, đặt chúng vào `backend/saved_model/`.
- Nếu cần cài `torch` với CUDA, làm theo hướng dẫn chính thức trên https://pytorch.org để chọn gói phù hợp.

2) Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend dev mặc định chạy trên http://localhost:3000; nếu cần gọi backend khác host/port, chỉnh `frontend/service/api.js`.

3) (Tùy chọn) Ứng dụng Java (BETQ)

Thư mục `BETQ/` là ứng dụng Spring Boot. Nếu không cần cho demo web, bạn có thể bỏ qua. Để chạy nếu cần: cài JDK 21 và dùng Maven hoặc `mvnw` có sẵn.

## Gợi ý khắc phục lỗi
- Nếu frontend không gọi được backend: kiểm tra backend đang chạy và cấu hình CORS.
- Nếu mô hình quá lớn: tải trước checkpoint vào `backend/saved_model/`.
- Luôn giữ API keys ngoài source; dùng biến môi trường hoặc `.env` (và thêm vào `.gitignore`).


## Checkpoint mô hình (Hugging Face Hub)

Các file mô hình lớn (checkpoint) không được lưu trong repo này mà được lưu riêng trên Hugging Face Hub. 

Tải model về thư mục `backend/saved_model/` (ví dụ):

1) Đăng nhập và chuẩn bị (chạy 1 lần):

```powershell
huggingface-cli login
git lfs install
```

2) Clone repo model (sử dụng Git LFS):

```powershell
git clone https://huggingface.co/quang14102004/bigfive_end
```
