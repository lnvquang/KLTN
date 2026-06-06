import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

MODEL_PATH = Path(os.getenv("PERSONALITY_MODEL_PATH", Path(__file__).resolve().parent / "saved_model"))
MULTITASK_MODEL_PATH = MODEL_PATH / "phobert_multitask_best (2).pt"
CLUSTER_MODEL_PATH = Path(os.getenv("CLUSTER_MODEL_PATH", MODEL_PATH / "hierarchical_cluster_model_core.pkl"))
CLUSTER_SCALER_PATH = Path(os.getenv("CLUSTER_SCALER_PATH", MODEL_PATH / "scaler.pkl"))
PHOBERT_NAME = "vinai/phobert-base"
MAX_LEN = 192

_tokenizer = None
_model = None
_multitask_tokenizer = None
_multitask_model = None
_cluster_model = None
_cluster_scaler = None

VIETNAMESE_STOPWORDS = {
    "và", "của", "là", "những", "các", "cho", "để", "với", "trong", "tại",
    "như", "nhưng", "vì", "thì", "mà", "hoặc", "nếu", "tuy", "đến", "bằng",
    "vẫn", "cứ", "chỉ", "lại", "thôi", "từng", "này", "kia", "đó", "đấy",
    "nào", "ai", "gì", "sao", "ở", "sau", "trước", "khi", "nhà", "người",
    "chuyện", "việc", "cái", "chiếc", "sự", "nỗi", "niềm", "sức"
}

TEENCODE_DICT = {
    "ko": "không", "k": "không", "khg": "không", "khum": "không", "kp": "không phải",
    "đg": "đang", "dg": "đang", "dc": "được", "đc": "được", "đt": "điện thoại",
    "j": "gì", "zi": "vậy", "v": "vậy", "vây": "vậy", "ntn": "như thế nào",
    "ok": "tốt", "oki": "tốt", "oke": "tốt", "gút": "tốt", "good": "tốt",
    "sad": "buồn", "happy": "vui", "iu": "yêu", "love": "yêu",
    "tks": "cảm ơn", "thanks": "cảm ơn", "tk": "cảm ơn", "cmon": "cảm ơn", "cmơn": "cảm ơn",
    "xl": "xin lỗi", "plz": "làm ơn", "please": "làm ơn",
    "b": "bạn", "bán": "bạn", "bn": "bạn", "c": "chị", "a": "anh", "e": "em",
    "m": "mình", "t": "tôi", "mn": "mọi người", "ng": "người", "gđ": "gia đình",
    "nv": "nhân viên", "shop": "cửa hàng", "st": "siêu thị", "kh": "khách hàng",
    "hnay": "hôm nay", "hqua": "hôm qua", "nt": "nhắn tin", "tl": "trả lời",
    "ib": "nhắn tin", "inbox": "nhắn tin", "rep": "trả lời", "fb": "facebook",
    "bit": "biết", "bít": "biết", " bik": "biết", "bh": "bây giờ", "h": "giờ",
    " bik": "biết", "mún": "muốn", "thik": "thích", "ty": "tình yêu",
    "chít": "chết", " lém": "lắm", " hỉu": "hiểu", " rùi": "rồi", " r": "rồi",
    " thui": "thôi", " đc ": " được ", " wa ": " quá ", " quá ": " quá ",
    " ship ": " giao hàng ", " shipper ": " người giao hàng ", " order ": " đặt hàng "
}


def _replace_teencode(text: str) -> str:
    words = text.split()
    return " ".join([TEENCODE_DICT.get(word, word) for word in words])


def preprocess_review_text(text: str) -> str:
    if text is None:
        return ""

    normalized_text = str(text).strip().lower()
    if not normalized_text or normalized_text == "nan":
        return ""

    normalized_text = unicodedata.normalize("NFC", normalized_text)
    normalized_text = re.sub(r"https?://\S+|www\.\S+", " ", normalized_text)
    normalized_text = re.sub(r"\S+@\S+", " ", normalized_text)
    normalized_text = re.sub(r"\b\d{8,}\b", " ", normalized_text)
    normalized_text = re.sub(r"([a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễđìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ])\1+", r"\1", normalized_text)
    normalized_text = re.sub(
        r"[^a-zA-Z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễđìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ\s]",
        " ",
        normalized_text,
    )
    normalized_text = re.sub(r"\s+", " ", normalized_text).strip()
    normalized_text = _replace_teencode(normalized_text)

    try:
        from pyvi import ViTokenizer
        normalized_text = ViTokenizer.tokenize(normalized_text)
    except Exception:
        pass
    print()

    filtered_words = [word for word in normalized_text.split() if word not in VIETNAMESE_STOPWORDS]
    return " ".join(filtered_words)

CLUSTER_LABELS = {
    0: "Nhóm 1: Chuyên gia đánh giá",
    1: "Nhóm 3: Khách hàng có tâm lý thoải mái",
    2: "Nhóm 2: Khách hàng có tiêu chuẩn cao",
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
        outputs = self.phobert(input_ids=input_ids, attention_mask=attention_mask)
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
        _multitask_model.phobert.load_state_dict({k.replace('phobert.', ''): v for k, v in state_dict.items() if k.startswith('phobert.')}, strict=False)
        _multitask_model.sentiment_head.load_state_dict({k.replace('sentiment_head.', ''): v for k, v in state_dict.items() if k.startswith('sentiment_head.')}, strict=False)
        _multitask_model.helpfulness_head.load_state_dict({k.replace('helpfulness_head.', ''): v for k, v in state_dict.items() if k.startswith('helpfulness_head.')}, strict=False)
        
        return _multitask_model, _multitask_tokenizer
    except Exception:
        return None, None


def load_cluster_model() -> Dict[str, object]:
    global _cluster_model, _cluster_scaler

    if isinstance(_cluster_model, dict) and "ready" in _cluster_model:
        return _cluster_model

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
            }
            break

        if hasattr(loaded, "predict"):
            scaler = None
            if CLUSTER_SCALER_PATH.exists():
                try:
                    scaler = joblib.load(CLUSTER_SCALER_PATH)
                except Exception:
                    scaler = None

            loaded_bundle = {
                "ready": True,
                "mode": "single",
                "source_path": str(model_path),
                "stage1_model": loaded,
                "stage1_scaler": scaler,
                "stage2_model": None,
                "stage2_scaler": None,
                "toxic_cluster_id": None,
                "casual_cluster_id": None,
                "expert_cluster_id": None,
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
            "message": "Không tìm thấy file hierarchical_cluster_model_core.pkl hoặc kmeans_model.pkl để gán cluster.",
        }

    _cluster_model = loaded_bundle
    _cluster_scaler = loaded_bundle.get("stage1_scaler")
    return loaded_bundle


def _predict_hierarchical_cluster(cluster_bundle: Dict[str, object], personality_scores: Dict[str, float], multitask_scores: Dict) -> Tuple[Optional[int], Optional[str]]:
    stage1_model = cluster_bundle.get("stage1_model")
    stage1_scaler = cluster_bundle.get("stage1_scaler")
    stage2_model = cluster_bundle.get("stage2_model")
    stage2_scaler = cluster_bundle.get("stage2_scaler")

    if stage1_model is None:
        return None, None

    sentiment = multitask_scores.get("sentiment", {})
    stage1_vector = np.array([[
        float(sentiment.get("negative", 0.0)),
        float(sentiment.get("neutral", 0.0)),
        float(sentiment.get("positive", 0.0)),
    ]], dtype=float)

    if stage1_scaler is not None:
        stage1_vector = stage1_scaler.transform(stage1_vector)

    stage1_cluster_id = int(stage1_model.predict(stage1_vector)[0])
    toxic_cluster_id = cluster_bundle.get("toxic_cluster_id")

    if toxic_cluster_id is not None and stage1_cluster_id == int(toxic_cluster_id):
        return 2, CLUSTER_LABELS[2]

    if stage2_model is None:
        return None, None

    stage2_vector = np.array([[
        float(personality_scores.get("openness", 0.0)),
        float(personality_scores.get("conscientiousness", 0.0)),
        float(personality_scores.get("extraversion", 0.0)),
        float(personality_scores.get("agreeableness", 0.0)),
        float(personality_scores.get("neuroticism", 0.0)),
        float(multitask_scores.get("helpfulness", {}).get("total", 0.0)),
        float(sentiment.get("positive", 0.0)),
    ]], dtype=float)

    if stage2_scaler is not None:
        stage2_vector = stage2_scaler.transform(stage2_vector)

    stage2_cluster_id = int(stage2_model.predict(stage2_vector)[0])
    casual_cluster_id = cluster_bundle.get("casual_cluster_id")

    if casual_cluster_id is not None and stage2_cluster_id == int(casual_cluster_id):
        return 1, CLUSTER_LABELS[1]

    return 0, CLUSTER_LABELS[0]


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
            scores = [float(v) for v in torch.softmax(logits, dim=-1)[0].tolist()]
    except Exception:
        try:
            scores = [float(v) for v in torch.softmax(logits, dim=-1)[0].tolist()]
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
            help_preds_clamped = torch.clamp(help_preds, 0.0, 1.0).cpu().numpy()[0]
            final_key_aspects_score = float(help_preds_clamped[0])
            final_advice_score = float(help_preds_clamped[1])
            final_helpfulness_total = (final_key_aspects_score + final_advice_score) / 2.0
            
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
        response["message"] = cluster_bundle.get("message") or "Không tìm thấy file hierarchical_cluster_model_core.pkl để gán cluster."
        return response

    try:
        cluster_id, cluster_label = _predict_hierarchical_cluster(cluster_bundle, personality_scores, multitask_scores)
        if cluster_id is None:
            response["message"] = "Không thể suy ra cluster từ model phân cụm đã tải."
            return response

        response["cluster"] = cluster_id
        response["cluster_label"] = cluster_label or CLUSTER_LABELS.get(cluster_id, f"Cụm {cluster_id}")
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