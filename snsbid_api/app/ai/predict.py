import joblib
import os
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

def load_model(bssamt: int, Aamt: int):
    if Aamt and Aamt > 0:
        model_file = "sns_random_sun.joblib"
    elif bssamt <= 1_000_000_000:
        model_file = "sns_random_10.joblib"
    elif bssamt <= 3_000_000_000:
        model_file = "sns_random_30.joblib"
    elif bssamt <= 5_000_000_000:
        model_file = "sns_random_50.joblib"
    else:
        model_file = "sns_random_50up.joblib"

    path = os.path.join(MODEL_DIR, model_file)
    return joblib.load(path), model_file.replace(".joblib", "")

def run_predict(bssamt: int, Aamt: int, realAmt: int,
                sucsfbidLwltRate: float = 0, bidNtceNm: str = ""):
    try:
        model, model_name = load_model(bssamt, Aamt)

        if Aamt and Aamt > 0:
            data = {
                "기초금액": bssamt,
                "하한율":   sucsfbidLwltRate,
                "A값":     bssamt,
                "순공사원가": Aamt,
            }
        else:
            data = {
                "기초금액": bssamt,
                "하한율":   sucsfbidLwltRate,
                "A값":     bssamt,
            }

        df = pd.DataFrame(data, index=[0])

        pred_amt = float(model.predict(df)[0])
        pred_rate = round((pred_amt / bssamt) * 100, 3) if bssamt else 0

        return {
            "predict_amt":  int(pred_amt),
            "predict_rate": pred_rate,
            "confidence":   0.0,
            "model_used":   model_name,
            "range": {
                "min": int(pred_amt * 0.99),
                "max": int(pred_amt * 1.01),
            }
        }
    except Exception as e:
        return {
            "predict_amt":  0,
            "predict_rate": 0,
            "confidence":   0,
            "model_used":   "error",
            "range":        {"min": 0, "max": 0},
            "error":        str(e),
        }