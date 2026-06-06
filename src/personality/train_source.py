import os
import re
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import StratifiedShuffleSplit
from transformers import XLMRobertaTokenizer, XLMRobertaModel, get_cosine_schedule_with_warmup
from tqdm import tqdm


#KHỞI TẠO BỘ TÁCH TỪ & PHÂN CHIA DỮ LIỆU (80/10/10)

model_name = "xlm-roberta-base" 
tokenizer = XLMRobertaTokenizer.from_pretrained(model_name)

# Nạp dữ liệu thô
df = pd.read_csv("D:/KLTN1/KLTN/data/pandora_300k.csv", encoding='utf-8-sig')

sss1 = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_idx, temp_idx in sss1.split(df, df['bin']):
    train_df = df.iloc[train_idx].copy()
    temp_df = df.iloc[temp_idx].copy()

sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
for val_idx, test_idx in sss2.split(temp_df, temp_df['bin']):
    val_df = temp_df.iloc[val_idx].copy()
    test_df = temp_df.iloc[test_idx].copy()


# ĐƯỜNG ỐNG TIỀN XỬ LÝ VĂN BẢN (PIPELINE)

MAX_LEN = 192

def maxlen(text):
    if pd.isna(text): 
        return ""
    words = str(text).split()
    truncated_text = " ".join(words[:MAX_LEN])
    return truncated_text 

def clean_text(text):
    if not isinstance(text, str): 
        return ""
    
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def basic_clean(text):
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r'[^\w\s\.\,\!\?\'\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip() 
    return text 

def full_preprocess_pipeline(text):
    text = maxlen(text)
    text = clean_text(text) 
    text = basic_clean(text)
    return text 

for d_frame in [train_df, test_df, val_df]:
    d_frame['text'] = d_frame['text'].apply(full_preprocess_pipeline)



# THIẾT LẬP PYTORCH DATASET CLASS

class TextRegressionDataset(Dataset):
    def __init__(self, dataframe, tokenizer, max_len=192):
        self.data = dataframe
        self.tokenizer = tokenizer
        self.max_len = max_len 

    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, index):
        row = self.data.iloc[index]
        text = str(row['text'])
        targets = torch.tensor([row['O'], row['C'], row['E'], row['A'], row['N']], dtype=torch.float)
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            add_special_tokens=True,      # Đảm bảo có token đầu <s> và cuối </s>
            return_token_type_ids=False,  # XLM-R không sử dụng Token Type IDs
            return_attention_mask=True,
            return_tensors='pt'
        ) 
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'targets': targets
        }

# Khởi tạo Datasets và DataLoaders (Test và Val set tắt shuffle để bảo toàn tính nhất quán)
train_dataset = TextRegressionDataset(train_df, tokenizer, max_len=MAX_LEN)
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)

val_dataset = TextRegressionDataset(val_df, tokenizer, max_len=MAX_LEN)
val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

test_dataset = TextRegressionDataset(test_df, tokenizer, max_len=MAX_LEN)
test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)


#KIẾN TRÚC MÔ HÌNH HỒI QUY ĐA ĐẦU RA TÙY CHỈNH

class XLMRobertaForMultiOutputRegression(nn.Module):
    def __init__(self, model_name, num_outputs=5, hidden_dim=256, dropout=0.3):
        super(XLMRobertaForMultiOutputRegression, self).__init__()
        self.encoder = XLMRobertaModel.from_pretrained(model_name)
         
        self.hidden_size = self.encoder.config.hidden_size
        self.intermediate = nn.Linear(self.hidden_size, hidden_dim) 
        self.dropout = nn.Dropout(dropout)
        self.regression_head = nn.Linear(hidden_dim, num_outputs)
        self.activation = nn.ReLU()  

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden = outputs.last_hidden_state
        
        # Áp dụng cơ chế Attention Masked Mean Pooling
        mask = attention_mask.unsqueeze(-1).float()
        pooled = (last_hidden * mask).sum(dim=1) / mask.sum(dim=1)
        
        x = self.activation(self.intermediate(pooled)) 
        x = self.dropout(x)
        predictions = self.regression_head(x)
        return predictions 



#TIẾN TRÌNH HUẤN LUYỆN VÀ ĐÁNH GIÁ (TRAINING LOOP)

model = XLMRobertaForMultiOutputRegression(model_name="xlm-roberta-base", num_outputs=5)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
 
# Bộ tối ưu hóa và các hàm mục tiêu đánh giá
optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.1)
loss_fn = nn.MSELoss() 
loss_fn_mae = nn.L1Loss()   # Thang đo MAE để theo dõi trực quan

epochs = 6
total_steps = len(train_loader) * epochs
scheduler = get_cosine_schedule_with_warmup(
    optimizer,
    num_warmup_steps=int(0.1 * total_steps),
    num_training_steps=total_steps
)

start_epoch = 0
best_val_loss = float('inf')

# Cơ chế khôi phục từ checkpoint nếu bị ngắt quãng
if os.path.exists('checkpoint.pt'):
    print("Loading checkpoint...")
    checkpoint = torch.load('checkpoint.pt', map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    start_epoch = checkpoint['epoch'] + 1
    best_val_loss = checkpoint['best_val_loss']
    print(f"Resuming from epoch {start_epoch}")
else:
    print("Starting fresh training")

# Vòng lặp huấn luyện chính
for epoch in range(start_epoch, epochs):
    # --- PHẦN HUẤN LUYỆN (TRAIN PHASE) ---
    model.train()
    total_loss = 0
    total_mae = 0
    progress_bar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{epochs}')
    for batch in progress_bar:
        optimizer.zero_grad()

        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        targets = batch['targets'].to(device)

        predictions = model(input_ids, attention_mask)
        loss = loss_fn(predictions, targets)
        total_loss += loss.item()
        
        loss_mae = loss_fn_mae(predictions, targets)
        total_mae += loss_mae.item()

        loss.backward()
        # Kẹp gradient ở ngưỡng chuẩn 5.0 để ổn định hóa lan truyền ngược
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()
        scheduler.step()
        progress_bar.set_postfix({'loss': f"{loss.item():.4f}"})

    avg_train_loss = total_loss / len(train_loader)
    avg_train_mae = total_mae / len(train_loader)

    # --- PHẦN ĐÁNH GIÁ (VALIDATION PHASE) ---
    model.eval()
    total_val_loss = 0
    total_val_mae = 0
    total_sq_error_per_col = torch.zeros(5, device=device)
    total_abs_error_per_col = torch.zeros(5, device=device)
    total_samples = 0

    val_bar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]")
    with torch.no_grad():
        for batch in val_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            targets = batch['targets'].to(device)

            predictions = model(input_ids, attention_mask)
            loss = loss_fn(predictions, targets)
            total_val_loss += loss.item()
            
            loss_mae_val = loss_fn_mae(predictions, targets)
            total_val_mae += loss_mae_val.item()

            # Tính toán sai số per-column phục vụ đánh giá chi tiết
            sq_error = (predictions - targets) ** 2
            abs_error = (predictions - targets).abs()
            total_sq_error_per_col += sq_error.sum(dim=0)
            total_abs_error_per_col += abs_error.sum(dim=0)
            total_samples += predictions.size(0)

            val_bar.set_postfix({'val_loss': f"{loss.item():.4f}"})

    avg_val_loss = total_val_loss / len(val_loader)
    avg_val_mae = total_val_mae / len(val_loader)
    mse_per_col = total_sq_error_per_col / total_samples
    mae_per_col = total_abs_error_per_col / total_samples

    print(f"\n--- Epoch {epoch+1} Metrics ---")
    print(f"Train Loss (MSE): {avg_train_loss:.4f} | Train MAE: {avg_train_mae:.4f}")
    print(f"Val Loss (MSE):   {avg_val_loss:.4f} | Val MAE:   {avg_val_mae:.4f}")
    print(f"MSE per column (OCEAN): {mse_per_col.cpu().numpy()}")
    print(f"MAE per column (OCEAN): {mae_per_col.cpu().numpy()}")

    # Đóng gói và lưu Checkpoint hiện tại
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'best_val_loss': best_val_loss,
    }
    torch.save(checkpoint, 'checkpoint.pt')

    # Cơ chế lưu trữ mô hình tối ưu nhất (Best Model) dựa trên Validation Loss
    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        torch.save(model.state_dict(), 'best_model.pt')
        print(f"  --> Saved best model checkpoint with Val Loss: {best_val_loss:.4f}")

print("Training pipeline finished successfully.")