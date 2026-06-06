import os
import re
import html
import unicodedata
import shutil
import numpy as np
import pandas as pd
from underthesea import word_tokenize

# ============================================================
# Adjusted local paths (relative to this file)
# ============================================================
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_HELP_DIR = os.path.join(ROOT, "data", "helpfulness")
INPUT_SENT_DIR = os.path.join(ROOT, "data", "sentiment")
STOPWORDS_PATH = os.path.join(ROOT, "data", "stopword", "vietnamese.txt")

FINAL_OUTPUT_DIR = os.path.join(ROOT, "backend_data", "final_model_data")
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

TEMP_HELP_DIR = os.path.join(ROOT, "backend_data", "temp_cleaned_helpfulness")
TEMP_SENT_DIR = os.path.join(ROOT, "backend_data", "temp_cleaned_sentiment")
os.makedirs(TEMP_HELP_DIR, exist_ok=True)
os.makedirs(TEMP_SENT_DIR, exist_ok=True)

# ============================================================
# Stopwords and teencode dict
# ============================================================
def load_stopwords(path=STOPWORDS_PATH):
    if not os.path.exists(path):
        print(f"Warning: Stopwords file not found: {path}")
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}

STOPWORDS = load_stopwords()

TEENCODE_DICT = {
    "ko": "không", "k": "không", "khong": "không", "hk": "không", "hem": "không",
    "hok": "không", "kg": "không", "kp": "không phải", "hong": "không", "khum": "không",
    "chx": "chưa", "cxk": "cũng không", "dc": "được", "dk": "được", "bt": "bình thường",
    "bth": "bình thường", "cx": "cũng", "vs": "với", "wa": "quá", "qa": "quá",
    "nt": "nhắn tin", "ib": "nhắn tin", "inb": "hộp thư", "ad": "quản trị viên",
    "mn": "mọi người", "mng": "mọi người", "mik": "mình", "mk": "mình", "mjk": "mình",
    "tui": "tôi", "toy": "tôi", "b": "bạn", "bn": "bạn", "bae": "bạn", "ny": "người yêu",
    "tks": "cảm ơn", "thx": "cảm ơn", "thanks": "cảm ơn", "thank": "cảm ơn", "camon": "cảm ơn",
    "j": "gì", "giz": "gì", "gik": "gì", "di": "gì", "s": "sao", "seo": "sao",
    "saoz": "sao", "nta": "người ta", "oke": "ok", "okie": "ok", "oki": "ok",
    "okela": "ok", "uh": "ừ", "uk": "ừ", "um": "ừ", "huhu": "buồn", "hic": "buồn",
    "hjx": "buồn", "haha": "cười", "kkk": "cười", "vl": "rất", "vkl": "rất", "cute": "dễ thương",
    "ms": "mới", "lun": "luôn", "luon": "luôn", "suotng": "suốt ngày", "sp": "sản phẩm",
    "shop": "cửa hàng", "sz": "size", "auth": "chính hãng", "rep": "trả lời", "tl": "trả lời",
    "nv": "nhân viên", "feedback": "phản hồi", "fb": "facebook", "freeship": "miễn phí vận chuyển",
    "ship": "giao hàng", "cod": "thanh toán khi nhận hàng", "sale": "giảm giá", "rv": "đánh giá",
    "rate": "đánh giá", "deal": "khuyến mãi", "outdate": "hết hạn", "date": "hạn sử dụng",
    "xịn": "tốt", "xin": "tốt", "xjn": "tốt", "xiu": "ít", "fake": "giả", "real": "thật",
    "best": "tốt nhất", "good": "tốt", "bad": "tệ", "nice": "tốt", "perfect": "hoàn hảo",
    "tr": "trời", "ưng": "thích"
}

# ============================================================
# Cleaning utilities
# ============================================================
def normalize_unicode(text):
    return unicodedata.normalize("NFC", text)

def remove_html_entities(text):
    return html.unescape(text)

def remove_urls(text):
    return re.sub(r"http\S+|www\.\S+", " ", text)

def remove_html_tags(text):
    return re.sub(r"<[^>]+>", " ", text)

def remove_latex(text):
    return re.sub(r"\$.*?\$|\\\\[a-zA-Z]+(\{.*?\})*", " ", text)

def remove_control_chars(text):
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

def reduce_repeated_chars(text):
    return re.sub(r"(.)\1{2,}", r"\1", text)

def normalize_punctuation(text):
    return re.sub(r"([!?.,])\1+", r"\1", text)

def normalize_special_symbols(text):
    replacements = {"@@": " bat ngo ", "&amp;amp;": " va ", "&amp;": " va ", "%": " phan tram ", "+": " cong ", "=": " bang "}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def remove_emojis(text):
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U000024C2-\U0001F251]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(" ", text)

def normalize_teencode(text):
    return " ".join([TEENCODE_DICT.get(word.lower(), word) for word in text.split()])

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = normalize_unicode(text)
    text = remove_html_entities(text)
    text = remove_html_tags(text)
    text = remove_urls(text)
    text = remove_latex(text)
    text = remove_control_chars(text)
    text = normalize_special_symbols(text)
    text = text.lower()
    text = normalize_teencode(text)
    text = remove_emojis(text)
    text = reduce_repeated_chars(text)
    text = normalize_punctuation(text)

    # Remove punctuation except Vietnamese characters and numbers
    text = re.sub(r"[^0-9a-zA-ZÀ-ỹà-ỹđĐ\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    try:
        text = word_tokenize(text, format="text")
    except Exception:
        pass

    return re.sub(r"\s+", " ", text).strip()


def process_helpfulness_file(file_name):
    input_path = os.path.join(INPUT_HELP_DIR, file_name)
    output_path = os.path.join(TEMP_HELP_DIR, file_name)

    try:
        df = pd.read_json(input_path)
    except Exception:
        df = pd.read_json(input_path, lines=True)

    if 'Comment' not in df.columns and 'Review' in df.columns:
        df = df.rename(columns={'Review': 'Comment'})

    df = df.dropna(subset=["Comment"])
    df["Comment"] = df["Comment"].apply(clean_text)
    df = df[df["Comment"].str.len() > 0]

    if 'KeyAspects' in df.columns:
        df["KeyAspects"] = pd.to_numeric(df["KeyAspects"], errors="coerce")
    else:
        df["KeyAspects"] = np.nan
    if 'DecisionMakingAdvice' in df.columns:
        df["DecisionMakingAdvice"] = pd.to_numeric(df["DecisionMakingAdvice"], errors="coerce")
    else:
        df["DecisionMakingAdvice"] = np.nan

    final_df = df[["Comment", "KeyAspects", "DecisionMakingAdvice"]].reset_index(drop=True)
    final_df.to_json(output_path, orient='records', force_ascii=False, indent=4)
    print(f"-> Đã làm sạch văn bản tập Hữu ích: {file_name} | Số mẫu: {len(final_df)}")


def process_sentiment_file(file_name):
    input_path = os.path.join(INPUT_SENT_DIR, file_name)
    output_path = os.path.join(TEMP_SENT_DIR, file_name)

    df = pd.read_csv(input_path)
    if 'comment' in df.columns and 'flag' in df.columns:
        df = df.rename(columns={'comment': 'Comment', 'flag': 'Sentiment'})
    elif 'Comment' not in df.columns and 'text' in df.columns:
        df = df.rename(columns={'text': 'Comment'})

    df = df.dropna(subset=["Comment"])
    df["Comment"] = df["Comment"].apply(clean_text)
    df = df[df["Comment"].str.len() > 0]

    if 'Sentiment' in df.columns:
        try:
            df["Sentiment"] = df["Sentiment"].astype(int)
        except Exception:
            df["Sentiment"] = pd.to_numeric(df["Sentiment"], errors='coerce').fillna(0).astype(int)
    else:
        df['Sentiment'] = 0

    final_df = df[['Comment', 'Sentiment']].reset_index(drop=True)
    final_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"-> Đã làm sạch văn bản tập Cảm xúc: {file_name} | Số mẫu: {len(final_df)}")
    return final_df


def merge_train_and_apply_masked_loss():
    # Read cleaned train data
    help_train_path = os.path.join(TEMP_HELP_DIR, "train.json")
    sent_train_path = os.path.join(TEMP_SENT_DIR, "train.csv")
    if not os.path.exists(help_train_path) or not os.path.exists(sent_train_path):
        raise FileNotFoundError("Cleaned train files not found in temp directories. Run cleaning first.")

    df_help_train = pd.read_json(help_train_path)
    df_sent_train = pd.read_csv(sent_train_path)

    # Apply masked-loss labels (-100) for missing-task fields
    df_help_train['Sentiment'] = -100
    df_sent_train['KeyAspects'] = -100.0
    df_sent_train['DecisionMakingAdvice'] = -100.0

    column_order = ['Comment', 'KeyAspects', 'DecisionMakingAdvice', 'Sentiment']
    df_help_train = df_help_train.reindex(columns=column_order)
    df_sent_train = df_sent_train.reindex(columns=column_order)

    train_merged_df = pd.concat([df_help_train, df_sent_train], axis=0, ignore_index=True)
    train_merged_df = train_merged_df.sample(frac=1, random_state=42).reset_index(drop=True)

    train_merged_df.to_json(os.path.join(FINAL_OUTPUT_DIR, "train_final.json"), orient='records', force_ascii=False, indent=4)
    print(f"-> Gộp thành công tập TRAIN hoàn chỉnh! Tổng số mẫu: {len(train_merged_df)}")

    # Copy dev/test cleaned files if exist
    paths = [
        (os.path.join(TEMP_HELP_DIR, "dev.json"), os.path.join(FINAL_OUTPUT_DIR, "dev_helpfulness.json")),
        (os.path.join(TEMP_HELP_DIR, "test.json"), os.path.join(FINAL_OUTPUT_DIR, "test_helpfulness.json")),
        (os.path.join(TEMP_SENT_DIR, "dev.csv"), os.path.join(FINAL_OUTPUT_DIR, "dev_sentiment.csv")),
        (os.path.join(TEMP_SENT_DIR, "test.csv"), os.path.join(FINAL_OUTPUT_DIR, "test_sentiment.csv")),
    ]
    for src, dst in paths:
        if os.path.exists(src):
            shutil.copy(src, dst)

    # Cleanup temp dirs
    try:
        shutil.rmtree(TEMP_HELP_DIR)
        shutil.rmtree(TEMP_SENT_DIR)
    except Exception:
        pass

    print(f"Đường dẫn thư mục chứa dữ liệu sẵn sàng của bạn: {FINAL_OUTPUT_DIR}")


if __name__ == "__main__":
    # Step 1: helpfulness
    print("--- 1. BẮT ĐẦU LÀM SẠCH VĂN BẢN TẬP HELPFULNESS ---")
    for f in ["train.json", "dev.json", "test.json"]:
        p = os.path.join(INPUT_HELP_DIR, f)
        if os.path.exists(p):
            process_helpfulness_file(f)
        else:
            print(f"Skip missing help file: {f}")

    # Step 2: sentiment
    print("\n--- 2. BẮT ĐẦU LÀM SẠCH VĂN BẢN TẬP CẢM XÚC ---")
    for f in ["train.csv", "dev.csv", "test.csv"]:
        p = os.path.join(INPUT_SENT_DIR, f)
        if os.path.exists(p):
            process_sentiment_file(f)
        else:
            print(f"Skip missing sent file: {f}")

    # Step 3: merge train with masked loss labels
    print("\n--- 3. GỘP TẬP TRAIN VÀ ÁP DỤNG MASKED LOSS ---")
    try:
        merge_train_and_apply_masked_loss()
    except FileNotFoundError as e:
        print(str(e))
