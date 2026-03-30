import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import ParameterGrid, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder
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

TRAIN_PATH = "../../pipeline_outputs/aim1_output/ukb_train_baseline.csv"  # change if needed
TEST_PATH = "../../pipeline_outputs/aim1_output/ukb_test_baseline.csv"    # change if needed
OUTPUT_DIR = Path("../../pipeline_outputs/aim4_output/RandomForest_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_TAG = "random_forest_baseline"  # change this for other datasets

N_SPLITS = 5
TEST_THRESHOLD = 0.5


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

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ]
    )
    return preprocessor



def build_model(params):
    return RandomForestClassifier(
        n_estimators=int(params["n_estimators"]),
        max_depth=params["max_depth"],
        min_samples_split=int(params["min_samples_split"]),
        min_samples_leaf=int(params["min_samples_leaf"]),
        max_features=params["max_features"],
        class_weight=params["class_weight"],
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
        "best_val_auc": float(val_auc),
    }



def fit_final_model(X_train_df, y_train, X_test_df, best_params):
    preprocessor = build_preprocessor(X_train_df)
    X_train_proc = preprocessor.fit_transform(X_train_df)
    X_test_proc = preprocessor.transform(X_test_df)

    final_model = build_model(best_params)
    final_model.fit(X_train_proc, y_train)

    return final_model, preprocessor, X_test_proc



def main():
    # =========================
    # Load data
    # =========================
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)

    X_train_full = train.drop(columns=[OUTCOME, EID])
    y_train_full = train[OUTCOME].astype(int)

    X_test = test.drop(columns=[OUTCOME, EID])
    y_test = test[OUTCOME].astype(int)

    print("Training data loaded:", X_train_full.shape)
    print("Test data loaded:", X_test.shape)

    # =========================
    # Hyperparameter grid
    # =========================
    param_grid = {
        "n_estimators": [300, 500],
        "max_depth": [None, 10, 20],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
        "max_features": ["sqrt", "log2"],
        "class_weight": [None, "balanced"],
    }

    grid = list(ParameterGrid(param_grid))
    print(f"Total hyperparameter combinations: {len(grid)}")

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

    # =========================
    # CV tuning on training set only
    # =========================
    all_results = []

    for combo_idx, params in enumerate(grid, start=1):
        print(f"\n===== Combination {combo_idx}/{len(grid)} =====")
        print(params)

        fold_aucs = []

        for fold, (tr_idx, val_idx) in enumerate(skf.split(X_train_full, y_train_full), start=1):
            print(f"  Fold {fold}/{N_SPLITS}")

            X_tr = X_train_full.iloc[tr_idx].copy()
            y_tr = y_train_full.iloc[tr_idx].copy()
            X_val = X_train_full.iloc[val_idx].copy()
            y_val = y_train_full.iloc[val_idx].copy()

            fold_result = train_one_fold(X_tr, y_tr, X_val, y_val, params)
            fold_aucs.append(fold_result["best_val_auc"])

            print(f"    Fold AUC: {fold_result['best_val_auc']:.4f}")

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

    results_csv = OUTPUT_DIR / f"{OUTPUT_TAG}_hyperparameter_search_results.csv"
    results_df.to_csv(results_csv, index=False)

    top10_csv = OUTPUT_DIR / f"{OUTPUT_TAG}_hyperparameter_top10.csv"
    results_df.head(10).to_csv(top10_csv, index=False)

    print("\nTop 10 combinations:")
    print(results_df.head(10))

    best_row = results_df.iloc[0].to_dict()
    best_params = {
        "n_estimators": int(best_row["n_estimators"]),
        "max_depth": None if pd.isna(best_row["max_depth"]) else int(best_row["max_depth"]),
        "min_samples_split": int(best_row["min_samples_split"]),
        "min_samples_leaf": int(best_row["min_samples_leaf"]),
        "max_features": str(best_row["max_features"]),
        "class_weight": None if pd.isna(best_row["class_weight"]) else best_row["class_weight"],
        "mean_cv_auc": float(best_row["mean_cv_auc"]),
        "std_cv_auc": float(best_row["std_cv_auc"]),
    }

    best_params_path = OUTPUT_DIR / f"{OUTPUT_TAG}_best_params.json"
    with open(best_params_path, "w") as f:
        json.dump(best_params, f, indent=4)

    print("\nBest parameters saved to:", best_params_path)
    print(json.dumps(best_params, indent=4))

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
    # Final fit on full training set + test evaluation
    # =========================
    print("\n===== Final training with best parameters =====")
    final_model, preprocessor, X_test_proc = fit_final_model(
        X_train_full,
        y_train_full,
        X_test,
        best_params,
    )

    test_probs = final_model.predict_proba(X_test_proc)[:, 1]
    test_preds = (test_probs >= TEST_THRESHOLD).astype(int)

    acc = accuracy_score(y_test, test_preds)
    prec = precision_score(y_test, test_preds, zero_division=0)
    rec = recall_score(y_test, test_preds, zero_division=0)
    f1 = f1_score(y_test, test_preds, zero_division=0)
    auc = roc_auc_score(y_test, test_probs)

    final_metrics = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "auc": float(auc),
        "threshold": float(TEST_THRESHOLD),
    }

    print("\n===== Random Forest Final Test Performance =====")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"AUC:       {auc:.4f}")

    metrics_txt_path = OUTPUT_DIR / f"{OUTPUT_TAG}_final_test_results.txt"
    with open(metrics_txt_path, "w", encoding="utf-8") as f:
        f.write("===== Best Hyperparameters =====\n")
        f.write(json.dumps(best_params, indent=4))
        f.write("\n\n===== Random Forest Final Test Performance =====\n")
        f.write(f"Accuracy:  {acc:.4f}\n")
        f.write(f"Precision: {prec:.4f}\n")
        f.write(f"Recall:    {rec:.4f}\n")
        f.write(f"F1:        {f1:.4f}\n")
        f.write(f"AUC:       {auc:.4f}\n")
        f.write(f"Threshold: {TEST_THRESHOLD:.2f}\n")

    metrics_json_path = OUTPUT_DIR / f"{OUTPUT_TAG}_final_test_metrics.json"
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_params": best_params,
                "final_test_metrics": final_metrics,
            },
            f,
            indent=4,
        )

    fpr, tpr, _ = roc_curve(y_test, test_probs)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"Random Forest (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Random Forest Final Test")
    plt.legend()
    plt.tight_layout()
    roc_path = OUTPUT_DIR / f"{OUTPUT_TAG}_final_test_roc_curve.png"
    plt.savefig(roc_path, dpi=300, bbox_inches="tight")
    plt.close()

    print("\nWorkflow complete.")
    print(f"Hyperparameter search results saved to: {results_csv}")
    print(f"Top 10 results saved to: {top10_csv}")
    print(f"Best params saved to: {best_params_path}")
    print(f"Final test metrics saved to: {metrics_txt_path}")
    print(f"Final test metrics JSON saved to: {metrics_json_path}")
    print(f"Ranking plot saved to: {ranking_path}")
    print(f"Final ROC curve saved to: {roc_path}")

    # saving auc metrics for overlay auc
    auc_path = Path("../../pipeline_outputs/aim4_output/auc_overlay")
    auc_path.mkdir(parents=True, exist_ok=True)

    df_auc = pd.DataFrame({
        "y_true": y_test,
        "y_pred": test_probs
    })

    df_auc.to_csv(auc_path / "rf_baseline.csv", index=False)


if __name__ == "__main__":
    main()
