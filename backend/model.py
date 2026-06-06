import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple
import html
import numpy as np

MODEL_PATH = Path(os.getenv("PERSONALITY_MODEL_PATH", Path(
    __file__).resolve().parent / "saved_model"))
MULTITASK_MODEL_PATH = MODEL_PATH / "phobert_multitask_best (2).pt"
CLUSTER_MODEL_PATH = Path(os.getenv(
    "CLUSTER_MODEL_PATH", MODEL_PATH / "hierarchical_clustering_model.pkl"))
CLUSTER_SCALER_PATH = Path(
    os.getenv("CLUSTER_SCALER_PATH", MODEL_PATH / "scaler.pkl"))
PHOBERT_NAME = "vinai/phobert-base"
MAX_LEN = 192

_tokenizer = None
_model = None
_multitask_tokenizer = None
_multitask_model = None
_cluster_model = None
_cluster_scaler = None


def _cluster_bundle_is_complete(bundle: Optional[Dict[str, object]]) -> bool:
    if not isinstance(bundle, dict):
        return False
    if bundle.get("mode") == "threshold_single":
        return all(bundle.get(key) is not None for key in ("stage2_model", "stage2_scaler"))
    return all(bundle.get(key) is not None for key in ("stage1_model", "stage1_scaler", "stage2_model", "stage2_scaler"))


VIETNAMESE_STOPWORDS = {
    "và", "của", "là", "những", "các", "cho", "để", "với", "trong", "tại",
    "như", "nhưng", "vì", "thì", "mà", "hoặc", "nếu", "tuy", "đến", "bằng",
    "vẫn", "cứ", "chỉ", "lại", "thôi", "từng", "này", "kia", "đó", "đấy",
    "nào", "ai", "gì", "sao", "ở", "sau", "trước", "khi", "nhà", "người",
    "chuyện", "việc", "cái", "chiếc", "sự", "nỗi", "niềm", "sức"
}

TEENCODE_DICT = {
    "kkkk": " cười ", "kkk": " cười ", "haha": " cười ", "huhu": " buồn ", "hic": " buồn ",
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
    "okela": "ok", "uh": "ừ", "uk": "ừ", "um": "ừ", "vl": "rất", "vkl": "rất", "cute": "dễ thương",
    "ms": "mới", "lun": "luôn", "luon": "luôn", "suotng": "suốt ngày", "sp": "sản phẩm",
    "shop": "cửa hàng", "sz": "size", "auth": "chính hãng", "rep": "trả lời", "tl": "trả lời",
    "nv": "nhân viên", "feedback": "phản hồi", "fb": "facebook", "freeship": "miễn phí vận chuyển",
    "ship": "giao hàng", "cod": "thanh toán khi nhận hàng", "sale": "giảm giá", "rv": "đánh giá",
    "rate": "đánh giá", "deal": "khuyến mãi", "outdate": "hết hạn", "date": "hạn sử dụng",
    "xịn": "tốt", "xin": "tốt", "xjn": "tốt", "xiu": "ít", "fake": "giả", "real": "thật",
    "best": "tốt nhất", "good": "tốt", "bad": "tệ", "nice": "tốt", "perfect": "hoàn hảo",
    "tr": "trời", "ưng": "thích"
}

EMOTICONS_DICT = {
    "=))": " cười_mỉa_mai_chê ", ":))": " cười_vui_hài_lòng ", "🙂": " cười_nhẹ_tạm_ổn ",
    "🙁": " buồn_thất_vọng ", "^^": " cười_tươi_ưng_ý ", "😣": " cực_kỳ_bực_mình ",
    "><": " quá_tệ_bực_mình ", ":<": " thất_vọng_chê ", "._.": " bối_rối_khó_hiểu ",
    "😑": " mệt_mỏi_thất_vọng ", "@@": " hoang_mang_ngỡ_ngàng "
}

EMOJI_DICT = {
    "🥰": " rất_thích ", "😍": " ưng_ý ", "🤣": " cười_vui ", "😂": " cười_vui ",
    "😀": " hài_lòng ", "😃": " vui_vẽ ", "😄": " hài_lòng ", "😁": " vui_lòng ",
    "😆": " rất_vui ", "😅": " nhẹ_nhõm ", "😊": " hài_lòng ", "🙂": " tạm_ổn ",
    "😋": " rất_ngon ", "🤤": " ngon_đỉnh ", "😎": " uy_tín ", "🤩": " quá_đẹp ", "🥳": " tuyệt_vời ",
    "😭": " quá_thất_vọng ", "😡": " cực_kỳ_tệ ", "😠": " không_hài_lòng ", "🤬": " quá_tệ_bực_mình ",
    "🙃": " mỉa_mai_chê ", "😒": " không_ưng_ý ", "😞": " thất_vọng ", "😔": " buồn_thất_vọng ",
    "😟": " lo_lắng_hàng_giả ", "😕": " không_đúng_mô_tả ", "🙁": " chê_hàng_kém ", "😫": " mệt_mỏi_quá ",
    "😩": " chán_nản ", "🥺": " thất_vọng_nhẹ ", "😢": " buồn_tiếc_tiền ", "😤": " bực_mình ",
    "🤯": " bực_nổ_não ", "😳": " ngỡ_ngàng_tệ ", "😱": " hoảng_hốt_tệ ",
    "👍": " chất_lượng_tốt ", "👎": " hàng_kém_chất_lượng ", "❤️": " rất_thích ", "💖": " yêu_thích ",
    "💝": " quà_tặng_kèm ", "🌟": " năm_sao_chất_lượng ", "⭐": " chất_lượng_cao ", "🔥": " cực_hot_đáng_mua ",
    "💯": " điểm_tuyệt_đối ", "❌": " lỗi_hỏng_không_mua ", "🚫": " cảnh_báo_tránh_xa ", "✅": " chuẩn_chính_hãng ", "✔️": " đúng_mô_tả "
}


def normalize_unicode(text): return unicodedata.normalize("NFC", text)
def remove_html_entities(text): return html.unescape(text)
def remove_urls(text): return re.sub(r"http\S+|www\.\S+", " ", text)
def remove_html_tags(text): return re.sub(r"<[^>]+>", " ", text)


def remove_latex(text): return re.sub(
    r"\$.*?\$|\\[a-zA-Z]+(\{.*?\})*", " ", text)


def remove_control_chars(text): return "".join(
    ch for ch in text if unicodedata.category(ch)[0] != "C")


def split_stuck_vietnamese_words(text):
    stuck_rules = [
        (r'chấtlượng', 'chất lượng'), (r'chaatslượng', 'chất lượng'),
        (r'hàngđẹp', 'hàng đẹp'), (r'giáhơi', 'giá hơi'),
        (r'giátốt', 'giá tốt'), (r'giahơi', 'giá hơi'),
        (r'shipnhanh', 'ship nhanh'), (r'đónggói', 'đóng gói'),
        (r'chấtlương', 'chất lượng'), (r'spchất', 'sản phẩm chất')
    ]
    for pattern, repl in stuck_rules:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def decode_telex_and_clean_tails(text):
    text = re.sub(r'\bchaats\b', 'chất', text)
    text = re.sub(r'\bchaat\b', 'chất', text)
    text = re.sub(r'\bchats\b', 'chất', text)
    text = re.sub(r'\bchasts\b', 'chất', text)
    text = re.sub(r'\bkems\b', 'kém', text)
    text = re.sub(r'\bnats\b', 'nát', text)
    text = re.sub(r'\bmacs\b', 'mắc', text)
    text = re.sub(r'\bdats\b', 'đắt', text)
    text = re.sub(r'\bgais\b', 'giả', text)
    text = re.sub(r'\bluaf\b', 'lừa', text)
    text = re.sub(r'\bcuif\b', 'cùi', text)
    text = re.sub(r'\bteef\b', 'tệ', text)
    text = re.sub(r'\bdeuf\b', 'đều', text)
    text = re.sub(r'\bbuonf\b', 'buồn', text)
    text = re.sub(r'\bteej\b', 'tệ', text)
    text = re.sub(r'\bnatj\b', 'nát', text)
    text = re.sub(r'\bcoj\b', 'cọ', text)
    text = re.sub(r'\bmeoj\b', 'móp', text)
    text = re.sub(r'\bbaoj\b', 'bảo', text)
    text = re.sub(r'\bthitj\b', 'thịt', text)
    text = re.sub(r'\bxuaf\b', 'xấu', text)
    text = re.sub(r'\bxaur\b', 'xấu', text)
    text = re.sub(r'\bloir\b', 'lỗi', text)
    text = re.sub(r'\bloix\b', 'lỗi', text)
    text = re.sub(r'\bhogr\b', 'hỏng', text)
    text = re.sub(r'\bhorgr\b', 'hỏng', text)
    text = re.sub(r'\bdepf\b', 'đẹp', text)
    text = re.sub(r'\bngonj\b', 'ngon', text)
    text = re.sub(r'\bngonf\b', 'ngon', text)
    text = re.sub(r'\bnhanhs\b', 'nhanh', text)
    text = re.sub(r'\btoots\b', 'tốt', text)
    text = re.sub(r'\btots\b', 'tốt', text)
    text = re.sub(r'\bref\b', 'rẻ', text)
    text = re.sub(r'\bthichs\b', 'thích', text)
    text = re.sub(r'\bungs\b', 'ưng', text)
    text = re.sub(r'\bchuans\b', 'chuẩn', text)
    text = re.sub(r'\bxems\b', 'xem', text)
    text = re.sub(r'\bmuas\b', 'mua', text)
    text = re.sub(r'\bguij\b', 'gửi', text)
    text = re.sub(r'\bdoif\b', 'đổi', text)
    text = re.sub(r'\btral\b', 'trả', text)
    text = re.sub(r'\bnhanj\b', 'nhận', text)
    text = re.sub(r'\bdongf\b', 'đóng', text)
    text = re.sub(
        r'([áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ])([sfrxj])(?=\s|$)', r'\1', text)
    return text


def reduce_repeated_chars(text):
    text = re.sub(
        r'([aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệoòóỏõọôồốộơờớởỡợuùúủũụưừứửữựiìíỉĩịyỳýỷỹỵ])\1+', r'\1', text)
    text = re.sub(r'(.)\1{1,}', r"\1", text)
    return text


def translate_lone_symbols(text):
    text = re.sub(r'\s+=\s+', ' bang ', text)
    text = text.replace("&amp;", " va ").replace("&", " va ").replace(
        "%", " phan tram ").replace("+", " cong ")
    return text


def translate_emojis(text):
    for emoji, text_rep in EMOJI_DICT.items():
        text = text.replace(emoji, text_rep)
    return text


def translate_emoticons_safe(text):
    sorted_emoticons = sorted(EMOTICONS_DICT.keys(), key=len, reverse=True)
    for emoti in sorted_emoticons:
        text = text.replace(emoti, f" {EMOTICONS_DICT[emoti]} ")
    return text


def normalize_teencode_only(text):
    words = text.split()
    return " ".join([TEENCODE_DICT.get(w.lower(), w) for w in words])


def _tokenize_text(text: str) -> str:
    # prefer underthesea, then pyvi, else fallback to simple whitespace tokenization
    try:
        from underthesea import word_tokenize as _ut_word_tokenize
        try:
            return _ut_word_tokenize(text, format="text")
        except TypeError:
            # older underthesea versions may not accept format kw
            return _ut_word_tokenize(text)
    except Exception:
        try:
            from pyvi.ViTokenizer import tokenize as _vi_tokenize
            return _vi_tokenize(text)
        except Exception:
            # fallback: collapse spaces (already lowercased earlier) and return
            return " ".join(text.split())


def clean_text(text):
    if text is None:
        return ""
    text = str(text)
    text = normalize_unicode(text)
    text = remove_html_entities(text)
    text = remove_html_tags(text)
    text = remove_urls(text)
    text = remove_latex(text)
    text = remove_control_chars(text)
    text = text.lower()
    text = translate_emoticons_safe(text)
    text = translate_emojis(text)
    text = split_stuck_vietnamese_words(text)
    text = decode_telex_and_clean_tails(text)
    text = reduce_repeated_chars(text)
    text = normalize_teencode_only(text)
    text = translate_lone_symbols(text)
    text = re.sub(r"[^0-9a-zA-ZÀ-ỹà-ỹđĐ\s_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = _tokenize_text(text)
    text = re.sub(r"\s+", " ", text).strip()
    filtered_words = [word for word in text.split(
    ) if word not in VIETNAMESE_STOPWORDS]
    return " ".join(filtered_words)


def preprocess_review_text(text: str) -> str:
    return clean_text(text)


class HierarchicalClusteringModel:
    def __init__(self):
        self.scaler1 = None
        self.kmeans1 = None
        self.scaler2 = None
        self.kmeans2 = None
        self.expert_cluster_id = None
        self.non_expert_cluster_id = None
        self.toxic_cluster_id = None
        self.casual_cluster_id = None

    def predict(self, ocean, helpfulness, sentiment_probs):
        p_tieucuc, p_tichcuc = sentiment_probs[0], sentiment_probs[2]
        conscientiousness = ocean[1]

        f_s1 = np.array([[helpfulness, conscientiousness]])
        f_s1_scaled = self.scaler1.transform(f_s1)
        pred_s1 = self.kmeans1.predict(f_s1_scaled)[0]

        if pred_s1 == self.expert_cluster_id:
            return "Nhóm 1: Chuyên gia đánh giá"

        neuroticism = ocean[4]
        f_s2 = np.array([[p_tieucuc, p_tichcuc, neuroticism]])
        f_s2_scaled = self.scaler2.transform(f_s2)
        pred_s2 = self.kmeans2.predict(f_s2_scaled)[0]

        if pred_s2 == self.toxic_cluster_id:
            return "Nhóm 2: Toxic / Khó tính"
        return "Nhóm 3: Người qua đường dễ dãi"


sys.modules.get("__main__", None) and setattr(
    sys.modules["__main__"], "HierarchicalClusteringModel", HierarchicalClusteringModel)

CLUSTER_LABELS = {

    0: "Cụm 0: Chuyên gia đánh giá",
    1: "Cụm 1: Khách hàng có tâm lý thoải mái",
    2: "Cụm 2: Khách hàng có tiêu chuẩn cao",
    
   
}


def default_personality_scores() -> Dict[str, float]:
    return {
        "openness": 0.0,
        "conscientiousness": 0.0,
        "extraversion": 0.0,
        "agreeableness": 0.0,
        "neuroticism": 0.0,
    }


def default_multitask_scores() -> Dict[str, float]:
    return {
        "sentiment": {
            "negative": 0.0,
            "neutral": 0.0,
            "positive": 0.0,
        },
        "helpfulness": {
            "key_aspects": 0.0,
            "advice": 0.0,
            "total": 0.0,
        }
    }


def default_review_analysis() -> Dict:
    return {
        "personality": default_personality_scores(),
        "multitask": default_multitask_scores(),
        "cluster": None,
        "cluster_label": None,
        "cluster_model_ready": False,
        "message": "Cluster model chưa được cấu hình hoặc chưa có file hierarchical_cluster_model_core.pkl.",
    }


def load_model() -> Tuple[Optional[object], Optional[object]]:
    global _model, _tokenizer
    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer

    if not MODEL_PATH.exists():
        return None, None

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        return None, None

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    _model.eval()
    return _model, _tokenizer


class PhoBertMultiTaskModel:
    """PhoBERT multitask model with sentiment and helpfulness heads."""

    def __init__(self, device="cpu"):
        import torch
        import torch.nn as nn
        from transformers import AutoModel

        self.device = device
        self.torch = torch
        self.nn = nn
        self.AutoModel = AutoModel

        # Define model architecture
        self.phobert = self.AutoModel.from_pretrained(PHOBERT_NAME)

        input_size = self.phobert.config.hidden_size  # 768
        mid_size = 384

        # Sentiment head: 3 classes (negative, neutral, positive)
        self.sentiment_head = self.nn.Sequential(
            self.nn.Linear(input_size, mid_size),
            self.nn.GELU(),
            self.nn.Dropout(0.1),
            self.nn.Linear(mid_size, 3)
        )

        # Helpfulness head: 2 outputs (key aspects, advice)
        self.helpfulness_head = self.nn.Sequential(
            self.nn.Linear(input_size, mid_size),
            self.nn.GELU(),
            self.nn.Dropout(0.1),
            self.nn.Linear(mid_size, 2)
        )

        self.to(device)
        self.eval()

    def forward(self, input_ids, attention_mask):
        outputs = self.phobert(input_ids=input_ids,
                               attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]

        sent_logits = self.sentiment_head(cls_output)
        help_preds = self.helpfulness_head(cls_output)

        return help_preds, sent_logits

    def to(self, device):
        self.device = device
        self.phobert.to(device)
        self.sentiment_head.to(device)
        self.helpfulness_head.to(device)
        return self

    def eval(self):
        self.phobert.eval()
        self.sentiment_head.eval()
        self.helpfulness_head.eval()
        return self


def load_multitask_model() -> Tuple[Optional[object], Optional[object]]:
    """Load PhoBERT multitask model (sentiment + helpfulness) and tokenizer."""
    global _multitask_model, _multitask_tokenizer

    if _multitask_model is not None and _multitask_tokenizer is not None:
        return _multitask_model, _multitask_tokenizer

    if not MULTITASK_MODEL_PATH.exists():
        return None, None

    try:
        import torch
        from transformers import AutoTokenizer
    except ImportError:
        return None, None

    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load tokenizer for PhoBERT multitask from HuggingFace
        _multitask_tokenizer = AutoTokenizer.from_pretrained(PHOBERT_NAME)
        _multitask_model = PhoBertMultiTaskModel(device=device)

        # Load weights from .pt file
        state_dict = torch.load(MULTITASK_MODEL_PATH, map_location=device)
        _multitask_model.phobert.load_state_dict({k.replace(
            'phobert.', ''): v for k, v in state_dict.items() if k.startswith('phobert.')}, strict=False)
        _multitask_model.sentiment_head.load_state_dict({k.replace(
            'sentiment_head.', ''): v for k, v in state_dict.items() if k.startswith('sentiment_head.')}, strict=False)
        _multitask_model.helpfulness_head.load_state_dict({k.replace(
            'helpfulness_head.', ''): v for k, v in state_dict.items() if k.startswith('helpfulness_head.')}, strict=False)

        return _multitask_model, _multitask_tokenizer
    except Exception:
        return None, None


def load_cluster_model() -> Dict[str, object]:
    global _cluster_model, _cluster_scaler

    if _cluster_bundle_is_complete(_cluster_model):
        return _cluster_model

    _cluster_model = None
    _cluster_scaler = None

    try:
        import joblib
    except ImportError:
        return {
            "ready": False,
            "mode": "unavailable",
            "message": "joblib is not installed.",
            "source_path": None,
            "stage1_model": None,
            "stage1_scaler": None,
            "stage2_model": None,
            "stage2_scaler": None,
            "toxic_cluster_id": None,
            "casual_cluster_id": None,
            "expert_cluster_id": None,
        }

    candidate_paths = []
    if os.getenv("CLUSTER_MODEL_PATH"):
        candidate_paths.append(CLUSTER_MODEL_PATH)
    else:
        candidate_paths.extend([
            MODEL_PATH / "hierarchical_clustering_model.pkl",
            MODEL_PATH / "hierarchical_cluster_model_core.pkl",
            MODEL_PATH / "kmeans_model.pkl",
        ])

    loaded_bundle = None
    for model_path in candidate_paths:
        if not Path(model_path).exists():
            continue

        try:
            loaded = joblib.load(model_path)
        except Exception as e:
            print("CLUSTER LOAD ERROR:", e)
            continue

        if hasattr(loaded, "scaler1") and hasattr(loaded, "kmeans1"):
            has_stage1 = getattr(loaded, "scaler1", None) is not None and getattr(
                loaded, "kmeans1", None) is not None
            has_stage2 = getattr(loaded, "scaler2", None) is not None and getattr(
                loaded, "kmeans2", None) is not None
            if has_stage1 and has_stage2:
                loaded_bundle = {
                    "ready": True,
                    "mode": "kaggle_object",
                    "source_path": str(model_path),
                    "stage1_model": loaded.kmeans1,
                    "stage1_scaler": loaded.scaler1,
                    "stage2_model": loaded.kmeans2,
                    "stage2_scaler": loaded.scaler2,
                    "toxic_cluster_id": getattr(loaded, "toxic_cluster_id", None),
                    "casual_cluster_id": getattr(loaded, "casual_cluster_id", None),
                    "expert_cluster_id": getattr(loaded, "expert_cluster_id", None),
                    "raw_bundle": loaded,
                }
                break

            loaded_bundle = {
                "ready": False,
                "mode": "incomplete_object",
                "source_path": str(model_path),
                "stage1_model": loaded.kmeans1 if getattr(loaded, "kmeans1", None) is not None else None,
                "stage1_scaler": loaded.scaler1 if getattr(loaded, "scaler1", None) is not None else None,
                "stage2_model": loaded.kmeans2 if getattr(loaded, "kmeans2", None) is not None else None,
                "stage2_scaler": loaded.scaler2 if getattr(loaded, "scaler2", None) is not None else None,
                "toxic_cluster_id": getattr(loaded, "toxic_cluster_id", None),
                "casual_cluster_id": getattr(loaded, "casual_cluster_id", None),
                "expert_cluster_id": getattr(loaded, "expert_cluster_id", None),
                "raw_bundle": loaded,
                "message": f"File {Path(model_path).name} đã load được nhưng thiếu scaler1/kmeans1/scaler2/kmeans2. Hãy export lại từ Kaggle sau khi gán đủ thuộc tính trước joblib.dump().",
            }
            break

        if hasattr(loaded, "scaler2") and hasattr(loaded, "kmeans2") and hasattr(loaded, "helpfulness_threshold") and hasattr(loaded, "c_threshold"):
            has_stage2 = getattr(loaded, "scaler2", None) is not None and getattr(
                loaded, "kmeans2", None) is not None
            if has_stage2:
                loaded_bundle = {
                    "ready": True,
                    "mode": "threshold_single",
                    "source_path": str(model_path),
                    "stage1_model": None,
                    "stage1_scaler": None,
                    "stage2_model": loaded.kmeans2,
                    "stage2_scaler": loaded.scaler2,
                    "toxic_cluster_id": getattr(loaded, "toxic_cluster_id", None),
                    "casual_cluster_id": getattr(loaded, "casual_cluster_id", None),
                    "expert_cluster_id": None,
                    "helpfulness_threshold": getattr(loaded, "helpfulness_threshold", 0.0),
                    "c_threshold": getattr(loaded, "c_threshold", 0.0),
                    "raw_bundle": loaded,
                }
                break

        if isinstance(loaded, dict) and {"kmeans1", "scaler1", "kmeans2", "scaler2"}.issubset(loaded.keys()):
            loaded_bundle = {
                "ready": True,
                "mode": "hierarchical",
                "source_path": str(model_path),
                "stage1_model": loaded.get("kmeans1"),
                "stage1_scaler": loaded.get("scaler1"),
                "stage2_model": loaded.get("kmeans2"),
                "stage2_scaler": loaded.get("scaler2"),
                "toxic_cluster_id": loaded.get("toxic_cluster_id"),
                "casual_cluster_id": loaded.get("casual_cluster_id"),
                "expert_cluster_id": loaded.get("expert_cluster_id"),
                "raw_bundle": loaded,
            }
            break

    if loaded_bundle is None:
        loaded_bundle = {
            "ready": False,
            "mode": "missing",
            "source_path": None,
            "stage1_model": None,
            "stage1_scaler": None,
            "stage2_model": None,
            "stage2_scaler": None,
            "toxic_cluster_id": None,
            "casual_cluster_id": None,
            "expert_cluster_id": None,
            "helpfulness_threshold": None,
            "c_threshold": None,
            "raw_bundle": None,
            "message": "Không tìm thấy file hierarchical_clustering_model.pkl, hierarchical_cluster_model_core.pkl hoặc kmeans_model.pkl để gán cluster.",
        }

    _cluster_model = loaded_bundle
    _cluster_scaler = loaded_bundle.get("stage1_scaler")
    return loaded_bundle


def _predict_hierarchical_cluster(cluster_bundle: Dict[str, object], personality_scores: Dict[str, float], multitask_scores: Dict) -> Tuple[Optional[int], Optional[str]]:
    raw_bundle = cluster_bundle.get("raw_bundle")
    if raw_bundle is not None and hasattr(raw_bundle, "scaler1") and hasattr(raw_bundle, "kmeans1"):
        stage1_model = raw_bundle.kmeans1
        stage1_scaler = raw_bundle.scaler1
        stage2_model = raw_bundle.kmeans2
        stage2_scaler = raw_bundle.scaler2
        expert_cluster_id = getattr(raw_bundle, "expert_cluster_id", None)
        toxic_cluster_id = getattr(raw_bundle, "toxic_cluster_id", None)
        casual_cluster_id = getattr(raw_bundle, "casual_cluster_id", None)
    elif raw_bundle is not None and hasattr(raw_bundle, "scaler2") and hasattr(raw_bundle, "kmeans2") and hasattr(raw_bundle, "helpfulness_threshold"):
        stage1_model = None
        stage1_scaler = None
        stage2_model = raw_bundle.kmeans2
        stage2_scaler = raw_bundle.scaler2
        expert_cluster_id = None
        toxic_cluster_id = getattr(raw_bundle, "toxic_cluster_id", None)
        casual_cluster_id = getattr(raw_bundle, "casual_cluster_id", None)
        helpfulness_threshold = float(
            getattr(raw_bundle, "helpfulness_threshold", 0.0))
        c_threshold = float(getattr(raw_bundle, "c_threshold", 0.0))
    else:
        stage1_model = cluster_bundle.get("stage1_model")
        stage1_scaler = cluster_bundle.get("stage1_scaler")
        stage2_model = cluster_bundle.get("stage2_model")
        stage2_scaler = cluster_bundle.get("stage2_scaler")
        expert_cluster_id = cluster_bundle.get("expert_cluster_id")
        toxic_cluster_id = cluster_bundle.get("toxic_cluster_id")
        casual_cluster_id = cluster_bundle.get("casual_cluster_id")
        helpfulness_threshold = float(
            cluster_bundle.get("helpfulness_threshold") or 0.0)
        c_threshold = float(cluster_bundle.get("c_threshold") or 0.0)

    if stage2_model is None or stage2_scaler is None:
        return None, None

    sentiment = multitask_scores.get("sentiment", {})
    helpfulness = float(multitask_scores.get(
        "helpfulness", {}).get("total", 0.0))
    conscientiousness = float(personality_scores.get("conscientiousness", 0.0))
    neuroticism = float(personality_scores.get("neuroticism", 0.0))

    if stage1_model is not None and stage1_scaler is not None:
        stage1_vector = np.array(
            [[helpfulness, conscientiousness]], dtype=float)
        stage1_vector = stage1_scaler.transform(stage1_vector)
        stage1_cluster_id = int(stage1_model.predict(stage1_vector)[0])

        if expert_cluster_id is not None and stage1_cluster_id == int(expert_cluster_id):
            return 0, CLUSTER_LABELS[0]
    else:
        if helpfulness >= helpfulness_threshold and conscientiousness >= c_threshold:
            return 0, CLUSTER_LABELS[0]

    stage2_vector = np.array([[
        float(sentiment.get("negative", 0.0)),
        float(sentiment.get("positive", 0.0)),
    ]], dtype=float)
    stage2_vector = stage2_scaler.transform(stage2_vector)
    stage2_cluster_id = int(stage2_model.predict(stage2_vector)[0])

    if toxic_cluster_id is not None and stage2_cluster_id == int(toxic_cluster_id):
        return 2, CLUSTER_LABELS[2]

    if casual_cluster_id is not None and stage2_cluster_id == int(casual_cluster_id):
        return 1, CLUSTER_LABELS[1]

    return 1, CLUSTER_LABELS[1]


def predict_personality(text: str, return_logits: bool = True) -> Dict[str, float]:
    """Predict personality traits for `text`.

    If `return_logits` is True (default) the function returns raw logits for
    each trait. If False it returns probabilities (sigmoid per-trait, with a
    softmax fallback).
    """
    model, tokenizer = load_model()
    if model is None or tokenizer is None:
        return default_personality_scores()

    try:
        import torch
    except ImportError:
        return default_personality_scores()

    cleaned_text = str(text or "").strip()

    inputs = tokenizer(
        cleaned_text,
        return_tensors="pt",
        truncation=True,
        padding=True,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    logits = getattr(outputs, "logits", None)
    if logits is None:
        return default_personality_scores()

    # Extract raw logits for the first (and only) example
    try:
        raw_logits = [float(x) for x in logits[0].tolist()]
    except Exception:
        return default_personality_scores()

    if return_logits:
        trait_names = [
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        ]
        return {name: value for name, value in zip(trait_names, raw_logits)}

    # Otherwise compute probabilities (sigmoid preferred, softmax fallback)
    try:
        sigmoid_probs = torch.sigmoid(logits)[0].tolist()
        if all(0.0 <= v <= 1.0 for v in sigmoid_probs):
            scores = [float(v) for v in sigmoid_probs]
        else:
            scores = [float(v)
                      for v in torch.softmax(logits, dim=-1)[0].tolist()]
    except Exception:
        try:
            scores = [float(v)
                      for v in torch.softmax(logits, dim=-1)[0].tolist()]
        except Exception:
            return default_personality_scores()

    trait_names = [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
    ]

    return {name: value for name, value in zip(trait_names, scores)}


def predict_multitask_scores(text: str, round_output: bool = True) -> Dict:
    """Predict sentiment and helpfulness using PhoBERT multitask model."""
    model, tokenizer = load_multitask_model()
    if model is None or tokenizer is None:
        return default_multitask_scores()

    try:
        import torch
        import torch.nn.functional as F
    except ImportError:
        return default_multitask_scores()

    try:
        device = model.device

        # Tokenize raw input to match the Kaggle training/evaluation pipeline.
        cleaned_text = str(text or "").strip()

        inputs = tokenizer(
            cleaned_text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=MAX_LEN
        )
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        # Run inference
        with torch.no_grad():
            help_preds, sent_logits = model.forward(input_ids, attention_mask)

            # --- Helpfulness (Regression) ---
            # Clamp outputs to [0, 1] range (matching training data range)
            help_preds_clamped = torch.clamp(
                help_preds, 0.0, 1.0).cpu().numpy()[0]
            final_key_aspects_score = float(help_preds_clamped[0])
            final_advice_score = float(help_preds_clamped[1])
            final_helpfulness_total = (
                final_key_aspects_score + final_advice_score) / 2.0

            # --- Sentiment (Classification) ---
            probabilities = F.softmax(sent_logits, dim=1)[0].cpu().numpy()
            prob_negative = float(probabilities[0])
            prob_neutral = float(probabilities[1])
            prob_positive = float(probabilities[2])
            sentiment_index = int(torch.argmax(sent_logits, dim=1)[0].item())

        if round_output:
            return {
                "sentiment": {
                    "negative": round(prob_negative, 2),
                    "neutral": round(prob_neutral, 2),
                    "positive": round(prob_positive, 2),
                },
                "sentiment_label": int(sentiment_index),
                "helpfulness": {
                    "key_aspects": round(final_key_aspects_score, 2),
                    "advice": round(final_advice_score, 2),
                    "total": round(final_helpfulness_total, 2),
                }
            }

        return {
            "sentiment": {
                "negative": prob_negative,
                "neutral": prob_neutral,
                "positive": prob_positive,
            },
            "sentiment_label": int(sentiment_index),
            "helpfulness": {
                "key_aspects": final_key_aspects_score,
                "advice": final_advice_score,
                "total": final_helpfulness_total,
            }
        }

    except Exception as e:
        return default_multitask_scores()


def _build_cluster_features(personality_scores: Dict[str, float], multitask_scores: Dict) -> Dict[str, float]:
    return {
        "O": float(personality_scores.get("openness", 0.0)),
        "C": float(personality_scores.get("conscientiousness", 0.0)),
        "E": float(personality_scores.get("extraversion", 0.0)),
        "A": float(personality_scores.get("agreeableness", 0.0)),
        "N": float(personality_scores.get("neuroticism", 0.0)),
        "Helpfulness": float(multitask_scores.get("helpfulness", {}).get("total", 0.0)),
        "Tích_cực": float(multitask_scores.get("sentiment", {}).get("positive", 0.0)),
        "Tiêu_cực": float(multitask_scores.get("sentiment", {}).get("negative", 0.0)),
        "Trung_tính": float(multitask_scores.get("sentiment", {}).get("neutral", 0.0)),
    }


def predict_review_analysis(text: str) -> Dict:
    # Also compute preprocessed text for inspection (does not change inference inputs)
    preprocessed_text = preprocess_review_text(text)

    personality_logits = predict_personality(text, return_logits=True)
    personality_scores = predict_personality(text, return_logits=False)
    multitask_scores = predict_multitask_scores(text, round_output=False)
    cluster_bundle = load_cluster_model()

    response = {
        "personality_logits": personality_logits,
        "personality_probs": personality_scores,
        "multitask": multitask_scores,
        "preprocessed_text": preprocessed_text,
        "cluster": None,
        "cluster_label": None,
        "cluster_model_ready": bool(cluster_bundle.get("ready")),
        "message": None,
    }

    if not cluster_bundle.get("ready"):
        response["message"] = cluster_bundle.get(
            "message") or "Không tìm thấy file hierarchical_cluster_model_core.pkl để gán cluster."
        return response

    try:
        cluster_id, cluster_label = _predict_hierarchical_cluster(
            cluster_bundle, personality_scores, multitask_scores)
        if cluster_id is None:
            response["message"] = (
                "Không thể suy ra cluster từ model phân cụm đã tải. "
                f"mode={cluster_bundle.get('mode')}, "
                f"stage1_model={cluster_bundle.get('stage1_model') is not None}, "
                f"stage1_scaler={cluster_bundle.get('stage1_scaler') is not None}, "
                f"stage2_model={cluster_bundle.get('stage2_model') is not None}, "
                f"stage2_scaler={cluster_bundle.get('stage2_scaler') is not None}"
            )
            return response

        response["cluster"] = cluster_id
        response["cluster_label"] = cluster_label or CLUSTER_LABELS.get(
            cluster_id, f"Cụm {cluster_id}")
    except Exception as e:
        response["cluster_model_ready"] = False
        response["message"] = f"Không thể suy ra cluster từ model phân cụm đã tải: {e}"

    return response


def check_tokenizers(verbose: bool = True) -> Dict[str, Dict]:
    """Return info about the tokenizers used by the saved model and PhoBERT.

    - saved_model tokenizer is expected to be an XLM-R tokenizer loaded from
      the `saved_model` folder (tokenizer.json / tokenizer_config.json).
    - PhoBERT tokenizer is loaded from `vinai/phobert-base`.

    This function imports `transformers.AutoTokenizer` lazily so it is safe to
    call even when `transformers` is not installed (it will return empty info).
    """
    info = {
        "saved_model": {},
        "phobert": {},
    }

    try:
        from transformers import AutoTokenizer
    except Exception:
        if verbose:
            print("transformers not available; cannot inspect tokenizers")
        return info

    # Saved-model tokenizer (local files)
    try:
        t_saved = AutoTokenizer.from_pretrained(MODEL_PATH)
        info["saved_model"] = {
            "name_or_path": getattr(t_saved, "name_or_path", None),
            "tokenizer_class": t_saved.__class__.__name__,
            "init_kwargs_keys": list(getattr(t_saved, "init_kwargs", {}).keys()),
        }
        if verbose:
            print("Saved-model tokenizer:")
            print(" ", info["saved_model"])
    except Exception as e:
        info["saved_model"] = {"error": str(e)}
        if verbose:
            print("Failed loading saved-model tokenizer:", e)

    # PhoBERT tokenizer (Hugging Face)
    try:
        t_phobert = AutoTokenizer.from_pretrained(PHOBERT_NAME)
        info["phobert"] = {
            "name_or_path": getattr(t_phobert, "name_or_path", None),
            "tokenizer_class": t_phobert.__class__.__name__,
            "init_kwargs_keys": list(getattr(t_phobert, "init_kwargs", {}).keys()),
        }
        if verbose:
            print("PhoBERT tokenizer:")
            print(" ", info["phobert"])
    except Exception as e:
        info["phobert"] = {"error": str(e)}
        if verbose:
            print("Failed loading PHOBERT tokenizer:", e)

    return info
