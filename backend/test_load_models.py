import traceback
import sys
from model import load_model, load_multitask_model

try:
    m, t = load_model()
    print("personality_model_loaded", m is not None and t is not None)
except Exception:
    print("personality_load_exception")
    traceback.print_exc()

try:
    mm, tt = load_multitask_model()
    print("multitask_model_loaded", mm is not None and tt is not None)
except Exception:
    print("multitask_load_exception")
    traceback.print_exc()

sys.exit(0)
