import os
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from sklearn.metrics import f1_score
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm.auto import tqdm
from sklearn.metrics import confusion_matrix, classification_report


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FINAL_OUTPUT_DIR = os.path.join(ROOT, "backend_data", "final_model_data")
FINAL_OUTPUT_DIR_01 = FINAL_OUTPUT_DIR

TOKENIZER_NAME = "vinai/phobert-base"
MAX_LEN = 128
BATCH_SIZE = 32

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"-> Thiết bị huấn luyện: {device}")

print("--- Đang nạp PhoBERT Tokenizer ---")
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)


class TrainMultiTaskDataset(Dataset):
    def __init__(self, df, tokenizer, max_len):
        self.df = df.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        row = self.df.iloc[index]
        comment = str(row.get('Comment', ""))

        encoding = self.tokenizer(
            comment,
            padding='max_length',
            truncation=True,
            max_length=self.max_len,
            return_tensors="pt"
        )

        key_aspects = row.get('KeyAspects', -100.0)
        advice = row.get('DecisionMakingAdvice', -100.0)
        sentiment = row.get('Sentiment', -100)

        if pd.isna(key_aspects):
            key_aspects = -100.0
        if pd.isna(advice):
            advice = -100.0
        if pd.isna(sentiment):
            sentiment = -100

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'key_aspects': torch.tensor(float(key_aspects), dtype=torch.float),
            'advice': torch.tensor(float(advice), dtype=torch.float),
            'sentiment': torch.tensor(int(sentiment), dtype=torch.long)
        }


class HelpfulnessEvalDataset(Dataset):
    def __init__(self, df, tokenizer, max_len):
        self.df = df.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        row = self.df.iloc[index]
        comment = str(row.get('Comment', ""))
        encoding = self.tokenizer(comment, padding='max_length', truncation=True, max_length=self.max_len, return_tensors="pt")

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'key_aspects': torch.tensor(float(row.get('KeyAspects', -100.0)), dtype=torch.float),
            'advice': torch.tensor(float(row.get('DecisionMakingAdvice', -100.0)), dtype=torch.float)
        }


class SentimentEvalDataset(Dataset):
    def __init__(self, df, tokenizer, max_len):
        self.df = df.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        row = self.df.iloc[index]
        comment = str(row.get('Comment', ""))
        encoding = self.tokenizer(comment, padding='max_length', truncation=True, max_length=self.max_len, return_tensors="pt")

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'sentiment': torch.tensor(int(row.get('Sentiment', -100)), dtype=torch.long)
        }


def safe_read_paths():
    # prefer the train_final.json produced by preprocessing
    train_path = os.path.join(FINAL_OUTPUT_DIR, "train_final.json")
    if not os.path.exists(train_path):
        # fallback to older names
        train_path = os.path.join(FINAL_OUTPUT_DIR, "train (2).json")

    dev_help_path = os.path.join(FINAL_OUTPUT_DIR, "dev_helpfulness.json")
    if not os.path.exists(dev_help_path):
        dev_help_path = os.path.join(FINAL_OUTPUT_DIR, "dev (2).json")

    dev_sent_path = os.path.join(FINAL_OUTPUT_DIR, "dev_sentiment.csv")
    if not os.path.exists(dev_sent_path):
        dev_sent_path = os.path.join(FINAL_OUTPUT_DIR_01, "dev (2).csv")

    return train_path, dev_help_path, dev_sent_path


def build_model(tokenizer_name, num_sentiment_classes):
    class PhoBERTMultiTaskModel(nn.Module):
        def __init__(self, model_name, num_sentiment_classes=3, dropout_rate=0.1):
            super(PhoBERTMultiTaskModel, self).__init__()
            self.phobert = AutoModel.from_pretrained(model_name)
            hidden_size = self.phobert.config.hidden_size
            self.dropout = nn.Dropout(dropout_rate)

            self.helpfulness_head = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(dropout_rate),
                nn.Linear(hidden_size // 2, 2)
            )

            self.sentiment_head = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(dropout_rate),
                nn.Linear(hidden_size // 2, num_sentiment_classes)
            )

        def forward(self, input_ids, attention_mask):
            outputs = self.phobert(input_ids=input_ids, attention_mask=attention_mask)
            cls_output = outputs[0][:, 0, :]
            cls_output = self.dropout(cls_output)

            help_logits = self.helpfulness_head(cls_output)
            sent_logits = self.sentiment_head(cls_output)

            return help_logits, sent_logits

    return PhoBERTMultiTaskModel(model_name=tokenizer_name, num_sentiment_classes=num_sentiment_classes)


def train():
    print("\n--- Đang nạp dữ liệu sạch vào DataLoader ---")
    train_path, dev_help_path, dev_sent_path = safe_read_paths()

    df_train = pd.read_json(train_path)
    df_dev_help = pd.read_json(dev_help_path)
    df_dev_sent = pd.read_csv(dev_sent_path)

    train_dataset = TrainMultiTaskDataset(df_train, tokenizer, MAX_LEN)
    dev_help_dataset = HelpfulnessEvalDataset(df_dev_help, tokenizer, MAX_LEN)
    dev_sent_dataset = SentimentEvalDataset(df_dev_sent, tokenizer, MAX_LEN)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    dev_help_loader = DataLoader(dev_help_dataset, batch_size=BATCH_SIZE, shuffle=False)
    dev_sent_loader = DataLoader(dev_sent_dataset, batch_size=BATCH_SIZE, shuffle=False)

    NUM_CLASSES = int(df_train[df_train['Sentiment'] != -100]['Sentiment'].nunique())
    model = build_model(TOKENIZER_NAME, NUM_CLASSES)
    model = model.to(device)

    # class weights from data
    sent_counts = df_train[df_train['Sentiment'] != -100]['Sentiment'].value_counts().sort_index()
    counts_list = [int(sent_counts.get(i, 0)) for i in range(NUM_CLASSES)]
    class_counts = torch.tensor(counts_list, dtype=torch.float)
    total_sent = class_counts.sum() if class_counts.sum() > 0 else torch.tensor(1.0)
    class_weights = (total_sent / (float(NUM_CLASSES) * (class_counts + 1e-8))).to(device)

    criterion_help = nn.MSELoss(reduction='none')
    criterion_sent = nn.CrossEntropyLoss(weight=class_weights, ignore_index=-100)

    WEIGHT_HELP = 1.0
    WEIGHT_SENT = 1.0

    def compute_multi_task_loss(help_preds, sent_logits, help_targets, sent_targets):
        key_aspects_pred = help_preds[:, 0]
        advice_pred = help_preds[:, 1]
        key_aspects_target, advice_target = help_targets

        help_mask = (key_aspects_target != -100.0).float()
        valid_help_samples = int(help_mask.sum().item())

        if valid_help_samples > 0:
            loss_key = torch.sum(criterion_help(key_aspects_pred, key_aspects_target) * help_mask) / (valid_help_samples + 1e-8)
            loss_adv = torch.sum(criterion_help(advice_pred, advice_target) * help_mask) / (valid_help_samples + 1e-8)
            loss_helpfulness = loss_key + loss_adv
        else:
            loss_helpfulness = torch.tensor(0.0, device=device)

        sent_mask = (sent_targets != -100)
        if sent_mask.sum().item() > 0:
            valid_idx = sent_mask.nonzero(as_tuple=True)[0]
            loss_sentiment = criterion_sent(sent_logits[valid_idx], sent_targets[valid_idx])
        else:
            loss_sentiment = torch.tensor(0.0, device=device)

        total_loss = torch.tensor(0.0, device=device)
        if valid_help_samples > 0:
            total_loss = total_loss + WEIGHT_HELP * loss_helpfulness
        if sent_mask.sum().item() > 0:
            total_loss = total_loss + WEIGHT_SENT * loss_sentiment

        return total_loss, (loss_helpfulness.item() if isinstance(loss_helpfulness, torch.Tensor) else float(loss_helpfulness)), (loss_sentiment.item() if isinstance(loss_sentiment, torch.Tensor) else float(loss_sentiment))

    # training config
    EPOCHS = 10
    LR = 2e-5

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(0.1 * total_steps), num_training_steps=total_steps)

    history_epoch = []
    history_train_mse = []
    history_dev_mse = []
    history_train_mae = []
    history_dev_mae = []

    best_combined_score = -float('inf')
    best_epoch = 0

    print(f"--- 🚀 BẮT ĐẦU TIẾN TRÌNH HUẤN LUYỆN CHUẨN {EPOCHS} EPOCHS ---")

    for epoch in range(EPOCHS):
        model.train()
        epoch_train_help_loss = 0.0
        epoch_train_help_mae = 0.0
        total_train_help_samples = 0

        train_bar = tqdm(train_loader, desc=f"Epoch [{epoch+1}/{EPOCHS}] - TRAIN", unit="batch")
        for step, batch in enumerate(train_bar):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            key_targets = batch['key_aspects'].to(device)
            adv_targets = batch['advice'].to(device)
            sent_targets = batch['sentiment'].to(device)

            help_preds, sent_logits = model(input_ids, attention_mask)

            loss, l_help, l_sent = compute_multi_task_loss(help_preds, sent_logits, (key_targets, adv_targets), sent_targets)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            help_mask = (key_targets != -100.0).float()
            valid_samples = int(help_mask.sum().item())
            if valid_samples > 0:
                epoch_train_help_loss += (l_help * valid_samples)
                mae_k = torch.sum(torch.abs(help_preds[:, 0] - key_targets) * help_mask).item()
                mae_a = torch.sum(torch.abs(help_preds[:, 1] - adv_targets) * help_mask).item()
                epoch_train_help_mae += (mae_k + mae_a)
                total_train_help_samples += valid_samples

            train_bar.set_postfix({
                "Loss": f"{loss.item():.4f}",
                "MSE_Help": f"{l_help:.4f}",
                "Loss_Sent": f"{l_sent:.4f}"
            })

        # evaluation
        model.eval()
        total_dev_mse = 0.0
        total_dev_mae = 0.0
        all_sent_preds, all_sent_targets = [], []

        with torch.no_grad():
            for batch in tqdm(dev_help_loader, desc=f"Epoch [{epoch+1}/{EPOCHS}] - EVAL HELP", unit="batch", leave=False):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                key_targets_dev = batch['key_aspects'].to(device)
                adv_targets_dev = batch['advice'].to(device)

                help_preds_dev, _ = model(input_ids, attention_mask)

                loss_k_mse = nn.functional.mse_loss(help_preds_dev[:, 0], key_targets_dev, reduction='mean')
                loss_a_mse = nn.functional.mse_loss(help_preds_dev[:, 1], adv_targets_dev, reduction='mean')
                total_dev_mse += (loss_k_mse + loss_a_mse).item()

                loss_k_mae = nn.functional.l1_loss(help_preds_dev[:, 0], key_targets_dev, reduction='mean')
                loss_a_mae = nn.functional.l1_loss(help_preds_dev[:, 1], adv_targets_dev, reduction='mean')
                total_dev_mae += (loss_k_mae + loss_a_mae).item()

            for batch in tqdm(dev_sent_loader, desc=f"Epoch [{epoch+1}/{EPOCHS}] - EVAL SENT", unit="batch", leave=False):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                targets_dev = batch['sentiment'].to(device)

                _, sent_logits_dev = model(input_ids, attention_mask)
                preds_dev = torch.argmax(sent_logits_dev, dim=1)

                all_sent_preds.extend(preds_dev.cpu().numpy())
                all_sent_targets.extend(targets_dev.cpu().numpy())

        num_dev_help_batches = len(dev_help_loader) if len(dev_help_loader) > 0 else 1

        current_train_mse = (epoch_train_help_loss / (total_train_help_samples + 1e-8)) / 2
        current_train_mae = (epoch_train_help_mae / (total_train_help_samples + 1e-8)) / 2
        current_dev_mse = total_dev_mse / (num_dev_help_batches * 2)
        current_dev_mae = total_dev_mae / (num_dev_help_batches * 2)

        try:
            current_dev_f1 = f1_score(all_sent_targets, all_sent_preds, average='macro')
        except Exception:
            current_dev_f1 = 0.0

        history_epoch.append(epoch + 1)
        history_train_mse.append(current_train_mse)
        history_dev_mse.append(current_dev_mse)
        history_train_mae.append(current_train_mae)
        history_dev_mae.append(current_dev_mae)

        combined_score = current_dev_f1 - current_dev_mse

        print(f"\n=======================================================")
        print(f" KẾT QUẢ ĐÁNH GIÁ CUỐI EPOCH [{epoch+1}/{EPOCHS}]")
        print(f" -> [HELP TRAIN] MSE: {current_train_mse:.4f} | MAE: {current_train_mae:.4f}")
        print(f" -> [HELP DEV]   MSE: {current_dev_mse:.4f} | MAE: {current_dev_mae:.4f}")
        print(f" -> [SENT DEV]   Macro F1: {current_dev_f1:.4f}")
        print(f" -> Điểm điều hướng Checkpoint: {combined_score:.4f}")

        if combined_score > best_combined_score:
            best_combined_score = combined_score
            best_epoch = epoch + 1
            save_path = os.path.join(ROOT, 'backend_data', 'phobert_multitask_best.pt')
            torch.save(model.state_dict(), save_path)
            print(f" >>> ĐÃ LƯU CHECKPOINT MODEL TỐT NHẤT TẠI EPOCH {best_epoch} <<<")
        print(f"=======================================================\n")

    print(f"--- ✅ HOÀN THÀNH HUẤN LUYỆN {EPOCHS} EPOCHS. TIẾN HÀNH DỰ ĐOÁN CUỐI ĐỂ XUẤT ĐỒ THỊ ---")

    # final evaluation using best model
    best_path = os.path.join(ROOT, 'backend_data', 'phobert_multitask_best.pt')
    if os.path.exists(best_path):
        model.load_state_dict(torch.load(best_path, map_location=device))
    model.eval()

    final_true_sent, final_pred_sent = [], []
    with torch.no_grad():
        for batch in tqdm(dev_sent_loader, desc="Đang trích xuất ma trận nhầm lẫn cuối cùng", unit="batch"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            _, sent_logits = model(input_ids, attention_mask)
            preds = torch.argmax(sent_logits, dim=1)
            final_true_sent.extend(batch['sentiment'].numpy())
            final_pred_sent.extend(preds.cpu().numpy())

    sent_labels = [f"Class {i}" for i in range(NUM_CLASSES)]

    fig, axes = plt.subplots(1, 3, figsize=(24, 6))

    cm_sent = confusion_matrix(final_true_sent, final_pred_sent)
    sns.heatmap(cm_sent, annot=True, fmt='d', cmap='Blues', ax=axes[0], xticklabels=sent_labels, yticklabels=sent_labels)
    axes[0].set_title(f'Mô hình Cảm xúc (Best Epoch: {best_epoch})\nMA TRẬN NHẦM LẪN', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Mô hình Dự đoán')
    axes[0].set_ylabel('Thực tế')

    axes[1].plot(history_epoch, history_train_mse, label='Train MSE', color='blue', linewidth=2, marker='o')
    axes[1].plot(history_epoch, history_dev_mse, label='Dev MSE', color='orange', linewidth=2, marker='s')
    axes[1].set_title('Đường cong Học tập: ĐỘ ĐO MSE (Helpfulness)', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Epochs')
    axes[1].set_ylabel('Giá trị Sai số (MSE)')
    axes[1].set_xticks(history_epoch)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(history_epoch, history_train_mae, label='Train MAE', color='green', linewidth=2, marker='o')
    axes[2].plot(history_epoch, history_dev_mae, label='Dev MAE', color='purple', linewidth=2, marker='s')
    axes[2].set_title('Đường cong Học tập: ĐỘ ĐO MAE (Helpfulness)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Epochs')
    axes[2].set_ylabel('Giá trị Sai số (MAE)')
    axes[2].set_xticks(history_epoch)
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    print("\n" + "="*60 + "\nBÁO CÁO PHÂN LOẠI CẢM XÚC CHI TIẾT TẠI CHECKPOINT TỐT NHẤT:\n" + "="*60)
    print(classification_report(final_true_sent, final_pred_sent, target_names=sent_labels, zero_division=0))


if __name__ == "__main__":
    train()
