"""Quick smoke test for the gradient boosting model."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import joblib
import pandas as pd
import warnings


BASE_DIR = Path(__file__).resolve().parent
COLUMNS_PATH = BASE_DIR / "columns_order.joblib"
MODEL_PATH = BASE_DIR / "gbt_model.joblib"


def _activate_first_dummy(columns: Iterable[str], prefix: str, frame: pd.DataFrame) -> None:
    """Turn on the first column that matches the provided prefix."""
    for column in columns:
        if column.startswith(prefix):
            frame[column] = 1
            return
    raise RuntimeError(f"No dummy column found for prefix '{prefix}'")


def build_sample_dataframe(columns: List[str]) -> pd.DataFrame:
    """Create a sample dataframe that follows the training column order."""
    sample_values = {
        "capital_cny_w": 500,
        "insured_number": 20,
        "invention_patent_applications": 5,
        "valid_invention_patents": 5,
        "valid_utility_models": 8,
        "valid_design_patents": 3,
        "software_copyrights": 4,
    }
    frame = pd.DataFrame([sample_values])

    # Activate known categorical dummies so the model receives a realistic row.
    _activate_first_dummy(columns, "city_district_", frame)
    _activate_first_dummy(columns, "type_", frame)
    _activate_first_dummy(columns, "industry_lv2_", frame)

    # 批量添加缺失的列，避免逐个添加导致的性能问题
    missing_cols = [col for col in columns if col not in frame.columns]
    frame[missing_cols] = 0

    return frame[columns]


def main() -> None:
    # 抑制pandas的性能警告
    warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

    columns: List[str] = joblib.load(COLUMNS_PATH)
    model = joblib.load(MODEL_PATH)

    sample = build_sample_dataframe(columns)
    prediction = float(model.predict(sample)[0])

    print("Model loaded successfully.")
    print(f"Predicted score for the sample row: {prediction:.2f}")


if __name__ == "__main__":
    main()
