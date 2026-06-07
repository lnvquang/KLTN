import os
import re
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
from transformers import AutoTokenizer, AutoConfig
from train_source import XLMRobertaForMultiOutputRegression

# Cấu hình thiết bị phần cứng
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
EPOCHS = 30  
BATCH_SIZE = 8
LR = 2e-5 
SAVE_PATH = "best_ocean_model1"

# Cấu hình Early Stopping để tránh quá khớp
PATIENCE = 3  
patience_counter = 0  


# 1. NẠP VÀ PHÂN CHIA DỮ LIỆU ĐÍCH (80/10/10)

file_path = "D:/KLTN1/KLTN/data/data_review_273_with_bigfive.csv" 
df = pd.read_csv(file_path, encoding='utf-8-sig')

traits = ['O', 'C', 'E', 'A', 'N']
X = df['text'].values
y = df[traits].values  # multi-label nhãn liên tục

# Chia Train (80%) và Temp (20%) bằng phân tầng đa nhãn
msss = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_idx, temp_idx in msss.split(X, y):
    train_df = df.iloc[train_idx].copy()
    temp_df = df.iloc[temp_idx].copy()

# Chia Temp thành Val (10% tổng) và Test (10% tổng)
X_temp = temp_df['text'].values
y_temp = temp_df[traits].values

msss2 = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
for val_idx, test_idx in msss2.split(X_temp, y_temp):
    val_df = temp_df.iloc[val_idx].copy()
    test_df = temp_df.iloc[test_idx].copy()

print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")



# ĐƯỜNG ỐNG TIỀN XỬ LÝ VĂN BẢN (PIPELINE)

MAX_LEN = 192

def maxlen(text):
    if pd.isna(text): return ""
    words = str(text).split()
    truncated_text = " ".join(words[:MAX_LEN])
    return truncated_text 

def clean_text(text):
    if not isinstance(text, str): return ""
    text = re.sub(r'https?://\S+|www\.\S+', '', text) # Xóa URL
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)        # Xóa markdown links
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def basic_clean(text):
    # Giữ nguyên chữ hoa/thường nguyên bản cho XLM-RoBERTa
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r'[^\w\s\.\,\!\?\'\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip() 
    return text 

def full_preprocess_pipeline(text):
    text = maxlen(text)
    text = clean_text(text) 
    text = basic_clean(text)
    return text 

# Áp dụng tiền xử lý dữ liệu tiếng Việt
for d_frame in [train_df, test_df, val_df]:
    d_frame['text'] = d_frame['text'].apply(full_preprocess_pipeline)



# 3. THIẾT LẬP DATASET & DATALOADER
class ReviewDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=192):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __getitem__(self, item):
        encoding = self.tokenizer(
            str(self.texts[item]),
            truncation=True,
            max_length=self.max_len,
            padding='max_length',
            return_tensors="pt"
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.labels[item], dtype=torch.float)
        }

    def __len__(self):
        return len(self.texts)

# Khởi tạo mô hình nền tảng và Tokenizer
base_model = "xlm-roberta-base"
tokenizer = AutoTokenizer.from_pretrained(base_model)
checkpoint_path = "D:/KLTN1/KLTN/backend/saved_model/checkpoint.pt"

# Nạp DataLoader (Test và Val set không sử dụng shuffle để nhất quán đánh giá)
train_loader = DataLoader(ReviewDataset(train_df['text'].tolist(), train_df[traits].values, tokenizer), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(ReviewDataset(val_df['text'].tolist(), val_df[traits].values, tokenizer), batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(ReviewDataset(test_df['text'].tolist(), test_df[traits].values, tokenizer), batch_size=BATCH_SIZE, shuffle=False)



# 4. KHỞI TẠO MÔ HÌNH & ĐÓNG BĂNG CHỌN LỌC
# Sử dụng lại kiến trúc source để tận dụng head H->256->5
model = XLMRobertaForMultiOutputRegression(model_name=base_model, num_outputs=5)

print("Đang nạp checkpoint nguồn (state_dict)...")
checkpoint = torch.load(checkpoint_path, map_location='cpu')
state_dict = checkpoint.get('model_state_dict', checkpoint.get('state_dict', checkpoint))
res = model.load_state_dict(state_dict, strict=False)
print('load_state_dict result:', res)

# Freeze toàn bộ tham số rồi mở một số tham số cuối để fine-tune nhẹ
for p in model.parameters():
    p.requires_grad = False

# Mở khóa các tham số trong encoder layer 11 (tên tham số chứa 'layer.11')
for name, p in model.encoder.named_parameters():
    if 'layer.11' in name:
        p.requires_grad = True

# Mở khóa head (intermediate + regression_head)
for p in model.intermediate.parameters():
    p.requires_grad = True
for p in model.regression_head.parameters():
    p.requires_grad = True

model.to(DEVICE)



# 5. BỘ TỐI ƯU HÓA VÀ HÀM LOSS ĐÁNH GIÁ (MAE L1Loss)
optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=LR)
criterion = torch.nn.L1Loss() # Sử dụng L1Loss (MAE) làm hàm loss chính

best_val_loss = float('inf')

print(f"Bắt đầu tinh chỉnh thích ứng trên {DEVICE}...")
for epoch in range(EPOCHS):
    model.train()
    train_loss = 0
    for batch in train_loader:
        optimizer.zero_grad()
        input_ids = batch['input_ids'].to(DEVICE)
        attention_mask = batch['attention_mask'].to(DEVICE)
        labels = batch['labels'].to(DEVICE)
        
        outputs = model(input_ids, attention_mask=attention_mask)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    avg_train_loss = train_loss / len(train_loader)

    # --- PHẦN KIỂM THỬ NỘI BỘ (VALIDATION PHASE) ---
    model.eval()
    val_loss = 0
    total_abs_error_per_col = torch.zeros(5, device=DEVICE)
    total_samples = 0
    
    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            labels = batch['labels'].to(DEVICE)
            
            outputs = model(input_ids, attention_mask=attention_mask)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            
            # SỬA LỖI: Tính toán cộng dồn sai số tuyệt đối cho từng cột OCEAN
            abs_error = (outputs - labels).abs()
            total_abs_error_per_col += abs_error.sum(dim=0)
            total_samples += labels.size(0)
            
    avg_val_loss = val_loss / len(val_loader)
    mae_per_col = total_abs_error_per_col / total_samples
    
    print(f"\nEpoch {epoch+1}/{EPOCHS} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
    print(f"MAE từng cột (O, C, E, A, N): {mae_per_col.cpu().numpy()}")

    # Kiểm tra cơ chế Early Stopping và Lưu trữ mô hình tốt nhất
    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        patience_counter = 0  # Reset bộ đếm nếu Val Loss cải thiện
        # Lưu model chuẩn Hugging Face
        model.save_pretrained(SAVE_PATH)
        tokenizer.save_pretrained(SAVE_PATH)
        print(f"Đã lưu model tốt nhất tại epoch {epoch+1} với Val Loss: {best_val_loss:.4f}")
    else:
        patience_counter += 1
        print(f"Val Loss không giảm. Early Stopping counter: {patience_counter}/{PATIENCE}")
        
        # Kích hoạt dừng sớm nếu vượt ngưỡng patience
        if patience_counter >= PATIENCE:
            print(f"ích hoạt Early Stopping! Dừng huấn luyện tại epoch {epoch+1}.")
            break

print(f"\nHoàn tất quá trình huấn luyện thích ứng liên ngôn ngữ!")