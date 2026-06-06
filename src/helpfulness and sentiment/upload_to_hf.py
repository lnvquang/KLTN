import os
from huggingface_hub import HfApi


def upload_folder_to_hf(repo_id, folder_path, token=None, commit_message="Upload model weights"):
    api = HfApi()
    api.create_repo(repo_id=repo_id, exist_ok=True, token=token)
    api.upload_folder(folder_path=folder_path, repo_id=repo_id, path_in_repo="", commit_message=commit_message, token=token)
    print(f"Uploaded folder {folder_path} -> https://huggingface.co/{repo_id}")


def upload_file_to_hf(repo_id, file_path, token=None, commit_message="Upload model file"):
    api = HfApi()
    api.create_repo(repo_id=repo_id, exist_ok=True, token=token)
    filename = os.path.basename(file_path)
    api.upload_file(path_or_fileobj=file_path, path_in_repo=filename, repo_id=repo_id, commit_message=commit_message, token=token)
    print(f"Uploaded file {file_path} -> https://huggingface.co/{repo_id}/blob/main/{filename}")


if __name__ == "__main__":
    print("This module provides upload_folder_to_hf and upload_file_to_hf helper functions.")
