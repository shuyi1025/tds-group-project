import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve
)
from xgboost import XGBClassifier

import os

output_dir = "../pipeline_outputs/aim4_output"
os.makedirs(output_dir, exist_ok=True)


outcome = "cvd_event"
eid = "eid"

# Load datasets

ukb_train = pd.read_csv("../pipeline_outputs/train_baseline_ee_onehot.csv")  #change file names accordingly
ukb_test = pd.read_csv("../pipeline_outputs/test_baseline_ee_onehot.csv")

# Split predictors and outcome
X_train = ukb_train.drop(columns=[outcome, eid])
y_train = ukb_train[outcome]

X_test = ukb_test.drop(columns=[outcome, eid])
y_test = ukb_test[outcome]

numeric_cols = X_train.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X_train.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

print("Number of numeric cols:", len(numeric_cols))
print("Number of categorical cols:", len(cat_cols))

preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
    ]
)

X_train_proc = preprocessor.fit_transform(X_train)
X_test_proc = preprocessor.transform(X_test)

print("Processed train shape:", X_train_proc.shape)
print("Processed test shape:", X_test_proc.shape)

n_pos = y_train.sum()
n_neg = len(y_train) - n_pos
scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

print("Positive cases in train:", int(n_pos))
print("Negative cases in train:", int(n_neg))
print("scale_pos_weight:", scale_pos_weight)


xgb_model = XGBClassifier(
    objective="binary:logistic",
    eval_metric="auc",
    n_estimators=300,
    learning_rate=0.05,
    max_depth=4,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.0,
    reg_lambda=1.0,
    scale_pos_weight=scale_pos_weight,
    random_state=123,
    n_jobs=-1
)


xgb_model.fit(X_train_proc, y_train)


test_probs = xgb_model.predict_proba(X_test_proc)[:, 1]
test_preds = (test_probs >= 0.5).astype(int)

acc = accuracy_score(y_test, test_preds)
prec = precision_score(y_test, test_preds, zero_division=0)
rec = recall_score(y_test, test_preds, zero_division=0)
f1 = f1_score(y_test, test_preds, zero_division=0)
auc = roc_auc_score(y_test, test_probs)

print("===== Logistic Regression Test Performance =====")
print(f"Accuracy:  {acc:.4f}")
print(f"Precision: {prec:.4f}")
print(f"Recall:    {rec:.4f}")
print(f"F1:        {f1:.4f}")
print(f"AUC:       {auc:.4f}")

result_path = os.path.join(output_dir, "xgboost_test_results_ee.txt")

with open(result_path, "w", encoding="utf-8") as f:
    f.write("===== XGBoost Test Performance =====\n")
    f.write(f"Accuracy:  {acc:.4f}\n")
    f.write(f"Precision: {prec:.4f}\n")
    f.write(f"Recall:    {rec:.4f}\n")
    f.write(f"F1:        {f1:.4f}\n")
    f.write(f"AUC:       {auc:.4f}\n\n")

print(f"Results saved to: {result_path}")


fpr, tpr, thresholds = roc_curve(y_test, test_probs)

plt.figure(figsize=(6, 5))
plt.plot(fpr, tpr, label=f"XGBoost (AUC = {auc:.3f})")
plt.plot([0, 1], [0, 1], linestyle="--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve - XGBoost")
plt.legend()
plt.tight_layout()
plt.show()

roc_path = os.path.join(output_dir, "xgboost_roc_curve_ee.png")
plt.savefig(roc_path, dpi=300, bbox_inches="tight")
plt.show()

print(f"ROC curve saved to: {roc_path}")