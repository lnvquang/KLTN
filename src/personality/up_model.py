from huggingface_hub import HfApi

# Khởi tạo API
api = HfApi()

# 1. Tạo một Repository mới trên Hugging Face
# Thay 'ten-tai-khoan-cua-ban' bằng username của bạn trên HF
repo_id = "quang14102004/bigfive_end"

api.create_repo(repo_id=repo_id, exist_ok=True)

# 2. Upload thư mục
api.upload_folder(
    folder_path="D:\\KLTN1\\KLTN\\backend\\saved_model\\", # Thư mục chứa model của bạn
    repo_id=repo_id,
    commit_message="Upload model weights"
)

print(f"Model đã được đẩy lên: https://huggingface.co/{repo_id}")