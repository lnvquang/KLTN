from model import load_model, MODEL_PATH
import torch

text = "Sản phẩm rất tốt, giao hàng nhanh"

model, tokenizer = load_model()
print('MODEL_PATH:', MODEL_PATH)
print('model:', type(model))
print('tokenizer class:', tokenizer.__class__.__name__)

inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
print('input_ids shape:', inputs['input_ids'].shape)
print('attention_mask shape:', inputs['attention_mask'].shape)

with torch.no_grad():
    outputs = model(**inputs)

print('outputs type:', type(outputs))
logits = getattr(outputs, 'logits', None)
print('logits is None?', logits is None)
if logits is not None:
    print('logits shape:', logits.shape)
    print('logits:', logits)
    # apply common transforms
    try:
        probs_sigmoid = torch.sigmoid(logits)[0].tolist()
    except Exception:
        probs_sigmoid = None
    try:
        probs_softmax = torch.softmax(logits, dim=-1)[0].tolist()
    except Exception:
        probs_softmax = None
    print('sigmoid probs (first example):', probs_sigmoid)
    print('softmax probs (first example):', probs_softmax)

# Inspect model config for label mapping
cfg = getattr(model, 'config', None)
print('\nmodel.config summary:')
if cfg is not None:
    try:
        print('  num_labels:', getattr(cfg, 'num_labels', None))
        print('  id2label:', getattr(cfg, 'id2label', None))
        print('  label2id:', getattr(cfg, 'label2id', None))
    except Exception as e:
        print('  failed to read config fields:', e)
else:
    print('  no config found')
