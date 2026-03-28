import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
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
    roc_curve
)

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

# Preprocessing pipelines
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

logit_model = LogisticRegression(
    penalty="l2",
    solver="liblinear",
    class_weight="balanced",
    max_iter=2000,
    random_state=123
)


clf = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", logit_model)
])

# Fit model on training data
clf.fit(X_train, y_train)

test_probs = clf.predict_proba(X_test)[:, 1]
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

result_path = os.path.join(output_dir, "logistic_test_results_ee.txt")

with open(result_path, "w", encoding="utf-8") as f:
    f.write("===== Logistic Regression Test Performance =====\n")
    f.write(f"Accuracy:  {acc:.4f}\n")
    f.write(f"Precision: {prec:.4f}\n")
    f.write(f"Recall:    {rec:.4f}\n")
    f.write(f"F1:        {f1:.4f}\n")
    f.write(f"AUC:       {auc:.4f}\n\n")

print(f"Results saved to: {result_path}")

fpr, tpr, thresholds = roc_curve(y_test, test_probs)

plt.figure(figsize=(6, 5))
plt.plot(fpr, tpr, label=f"Logistic Regression (AUC = {auc:.3f})")
plt.plot([0, 1], [0, 1], linestyle="--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve - Logistic Regression")
plt.legend()
plt.tight_layout()
plt.show()

roc_path = os.path.join(output_dir, "logistic_roc_curve_ee.png")
plt.savefig(roc_path, dpi=300, bbox_inches="tight")
plt.show()

print(f"ROC curve saved to: {roc_path}")