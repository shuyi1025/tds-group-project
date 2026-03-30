import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.model_selection import ParameterGrid, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# =========================
# Settings
# =========================
SEED = 42
OUTCOME = "cvd_event"
EID = "eid"

TRAIN_PATH = "../../pipeline_outputs/aim1_output/train_baseline_ee_onehot.csv"   # change if needed
TEST_PATH = "../../pipeline_outputs/aim1_output/test_baseline_ee_onehot.csv"     # change if needed
OUTPUT_DIR = Path("../../pipeline_outputs/aim4_output/logistic_outputs")
OUTPUT_TAG = "logistic_ee"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N_SPLITS = 5
MAX_ITER = 5000


# =========================
# Reproducibility
# =========================
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)


set_seed(SEED)


# =========================
# Utilities
# =========================
def build_preprocessor(X_df):
    numeric_cols = X_df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    cat_cols = X_df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, cat_cols),
        ]
    )

    return preprocessor


def build_model(params):
    return LogisticRegression(
        penalty=params["penalty"],
        C=params["C"],
        solver=params["solver"],
        class_weight=params["class_weight"],
        l1_ratio=params.get("l1_ratio", None),
        max_iter=MAX_ITER,
        random_state=SEED,
        n_jobs=-1,
    )


def train_one_fold(X_train_df, y_train, X_val_df, y_val, params):
    preprocessor = build_preprocessor(X_train_df)
    X_train_proc = preprocessor.fit_transform(X_train_df)
    X_val_proc = preprocessor.transform(X_val_df)

    model = build_model(params)
    model.fit(X_train_proc, y_train)

    val_probs = model.predict_proba(X_val_proc)[:, 1]
    val_auc = roc_auc_score(y_val, val_probs)

    return {
        "val_auc": float(val_auc)
    }


def main():
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)

    X = train.drop(columns=[OUTCOME, EID])
    y = train[OUTCOME].astype(int)

    X_test = test.drop(columns=[OUTCOME, EID])
    y_test = test[OUTCOME].astype(int)

    print("Training data loaded:", X.shape)
    print("Test data loaded:", X_test.shape)

    # Compatible parameter grids only
    param_grid = [
        {
            "penalty": ["l2"],
            "C": [0.001, 0.01, 0.1, 1, 10, 100],
            "class_weight": [None, "balanced"],
            "solver": ["lbfgs"],
        },
        {
            "penalty": ["l1"],
            "C": [0.001, 0.01, 0.1, 1, 10],
            "class_weight": [None, "balanced"],
            "solver": ["liblinear"],
        },
        {
            "penalty": ["elasticnet"],
            "C": [0.01, 0.1, 1, 10],
            "class_weight": [None, "balanced"],
            "solver": ["saga"],
            "l1_ratio": [0.2, 0.5, 0.8],
        },
    ]

    grid = list(ParameterGrid(param_grid))
    print(f"Total hyperparameter combinations: {len(grid)}")

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

    all_results = []

    for combo_idx, params in enumerate(grid, start=1):
        print(f"\n===== Combination {combo_idx}/{len(grid)} =====")
        print(params)

        fold_aucs = []

        for fold, (tr_idx, val_idx) in enumerate(skf.split(X, y), start=1):
            print(f"  Fold {fold}/{N_SPLITS}")

            X_tr = X.iloc[tr_idx].copy()
            y_tr = y.iloc[tr_idx].copy()
            X_val = X.iloc[val_idx].copy()
            y_val = y.iloc[val_idx].copy()

            fold_result = train_one_fold(X_tr, y_tr, X_val, y_val, params)
            fold_aucs.append(fold_result["val_auc"])

            print(f"    Fold AUC: {fold_result['val_auc']:.4f}")

        result_row = {
            **params,
            "mean_cv_auc": float(np.mean(fold_aucs)),
            "std_cv_auc": float(np.std(fold_aucs)),
        }
        all_results.append(result_row)

    results_df = pd.DataFrame(all_results).sort_values(
        by=["mean_cv_auc", "std_cv_auc"],
        ascending=[False, True],
    ).reset_index(drop=True)

    # Save full search results
    results_csv = OUTPUT_DIR / f"{OUTPUT_TAG}_hyperparameter_search_results.csv"
    results_df.to_csv(results_csv, index=False)

    print("\nTop 10 combinations:")
    print(results_df.head(10))

    # Save top 10 separately
    top10_csv = OUTPUT_DIR / f"{OUTPUT_TAG}_hyperparameter_top10.csv"
    results_df.head(10).to_csv(top10_csv, index=False)

    best_row = results_df.iloc[0].to_dict()
    best_params = {
        "penalty": best_row["penalty"],
        "C": float(best_row["C"]),
        "solver": best_row["solver"],
        "class_weight": best_row["class_weight"],
        "l1_ratio": None if pd.isna(best_row.get("l1_ratio", np.nan)) else float(best_row["l1_ratio"]),
        "mean_cv_auc": float(best_row["mean_cv_auc"]),
        "std_cv_auc": float(best_row["std_cv_auc"]),
    }

    best_params_path = OUTPUT_DIR / f"{OUTPUT_TAG}_best_params.json"
    with open(best_params_path, "w", encoding="utf-8") as f:
        json.dump(best_params, f, indent=4)

    print("\nBest parameters saved to:", best_params_path)
    print(json.dumps(best_params, indent=4))

    # Plot top 15 AUCs
    top_n = min(15, len(results_df))
    plt.figure(figsize=(10, 5))
    plt.plot(
        range(1, top_n + 1),
        results_df.loc[: top_n - 1, "mean_cv_auc"].values,
        marker="o",
    )
    plt.xlabel("Ranked hyperparameter combination")
    plt.ylabel("Mean CV AUC")
    plt.title("Top Hyperparameter Combinations by Mean CV AUC")
    plt.tight_layout()
    ranking_path = OUTPUT_DIR / f"{OUTPUT_TAG}_hyperparameter_ranking.png"
    plt.savefig(ranking_path, dpi=300)
    plt.close()

    # =========================
    # Final train on full train set and evaluate on test set
    # =========================
    print("\n===== Final training with best parameters =====")

    final_preprocessor = build_preprocessor(X)
    X_train_proc = final_preprocessor.fit_transform(X)
    X_test_proc = final_preprocessor.transform(X_test)

    final_model = build_model(best_params)
    final_model.fit(X_train_proc, y)

    test_probs = final_model.predict_proba(X_test_proc)[:, 1]
    test_preds = (test_probs >= 0.5).astype(int)

    acc = accuracy_score(y_test, test_preds)
    prec = precision_score(y_test, test_preds, zero_division=0)
    rec = recall_score(y_test, test_preds, zero_division=0)
    f1 = f1_score(y_test, test_preds, zero_division=0)
    auc = roc_auc_score(y_test, test_probs)

    print("\n===== Logistic Regression Final Test Performance =====")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"AUC:       {auc:.4f}")

    results_txt_path = OUTPUT_DIR / f"{OUTPUT_TAG}_final_test_results.txt"
    with open(results_txt_path, "w", encoding="utf-8") as f:
        f.write("===== Logistic Regression Final Test Performance =====\n")
        f.write(f"Accuracy:  {acc:.4f}\n")
        f.write(f"Precision: {prec:.4f}\n")
        f.write(f"Recall:    {rec:.4f}\n")
        f.write(f"F1:        {f1:.4f}\n")
        f.write(f"AUC:       {auc:.4f}\n\n")
        f.write("Best parameters used:\n")
        json.dump(best_params, f, indent=4)

    metrics_json = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "auc": float(auc),
        "best_params": best_params,
    }
    metrics_json_path = OUTPUT_DIR / f"{OUTPUT_TAG}_final_test_metrics.json"
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=4)

    fpr, tpr, _ = roc_curve(y_test, test_probs)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"Logistic Regression (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Logistic Regression")
    plt.legend()
    plt.tight_layout()
    roc_path = OUTPUT_DIR / f"{OUTPUT_TAG}_final_test_roc_curve.png"
    plt.savefig(roc_path, dpi=300)
    plt.close()

    print("\nAll outputs saved to:", OUTPUT_DIR.resolve())
    print("Saved files:")
    print(" -", results_csv.name)
    print(" -", top10_csv.name)
    print(" -", best_params_path.name)
    print(" -", ranking_path.name)
    print(" -", results_txt_path.name)
    print(" -", metrics_json_path.name)
    print(" -", roc_path.name)


  # saving auc metrics for overlay auc
    auc_path = Path("../../pipeline_outputs/aim4_output/auc_overlay")
    auc_path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "y_true": y_test,
        "y_pred": test_probs
    })

    df.to_csv(auc_path / "logistic_baseline_ee.csv", index=False)





if __name__ == "__main__":
    main()
